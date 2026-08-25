"""
Upload service – processes CSV bulk upload of material data.
"""
from __future__ import annotations

import io
import re
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.material import Material, MaterialStatus
from app.models.material_attribute import MaterialAttribute
from app.models.material_embedding import MaterialEmbedding
from app.models.upload_job import UploadJob, UploadStatus
from app.core.config import settings

# Expected CSV columns (case-insensitive)
REQUIRED_COLUMNS = {"legacy_material_code", "original_description"}
OPTIONAL_COLUMNS = {"category_id", "unit_of_measure", "manufacturer"}

logger = logging.getLogger(__name__)


def _read_csv_df(content: bytes) -> "pd.DataFrame":
    """Read CSV bytes into a DataFrame using utf-8-sig and normalize headers.

    This handles BOM, trims whitespace, lower-cases and replaces spaces with
    underscores so header matching is robust.
    """
    # Decode with utf-8-sig to remove BOM if present
    text = content.decode("utf-8-sig")

    # Some CSVs incorrectly wrap the entire line in quotes, producing a
    # single field like '"col1,col2"'. Detect that case and unwrap lines
    # so pandas can parse the proper comma-separated columns.
    lines = text.splitlines()
    non_empty = [l for l in lines if l.strip()]
    if non_empty and all(l.startswith('"') and l.endswith('"') for l in non_empty):
        logger.info("Detected whole-line quoted CSV; unwrapping lines for parsing")
        unwrapped = [l[1:-1] for l in non_empty]
        text_to_parse = "\n".join(unwrapped)
    else:
        text_to_parse = text

    df = pd.read_csv(io.StringIO(text_to_parse))
    # Normalize column names: strip, lower, replace spaces with underscores
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    logger.info("Parsed CSV columns: %s", list(df.columns))
    return df


def _storage_object_name(job_id: int, file_name: str) -> str:
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", file_name)
    return f"uploads/{job_id}/{safe_name}"


def store_original_csv(job_id: int, file_name: str, content: bytes) -> str | None:
    """Store the original validated CSV without exposing Supabase keys to React."""
    if settings.storage_backend.lower() == "local":
        target = Path(settings.upload_dir) / _storage_object_name(job_id, file_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)
    if not settings.supabase_url or not settings.supabase_service_role_key:
        # Storage is optional. Database processing remains available when a
        # demo only supplies the database URL/anon key.
        return None
    from supabase import create_client
    client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    object_name = _storage_object_name(job_id, file_name)
    try:
        client.storage.create_bucket(settings.supabase_storage_bucket, {"public": False})
    except Exception:
        pass  # Bucket already exists, or policy forbids bucket creation.
    client.storage.from_(settings.supabase_storage_bucket).upload(
        object_name, content, {"content-type": "text/csv", "upsert": "true"}
    )
    return object_name


async def create_upload_job(
    db: AsyncSession, cpse_id: int, file_name: str, uploaded_by: int | None = None
) -> UploadJob:
    job = UploadJob(
        cpse_id=cpse_id,
        uploaded_by=uploaded_by,
        file_name=file_name,
        status=UploadStatus.PENDING,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def process_csv_upload(
    db: AsyncSession, job_id: int, content: bytes
) -> UploadJob:
    """
    Parse CSV content and bulk-insert Material rows.
    Updates the UploadJob with progress and final status.
    """
    # Load job
    result = await db.execute(select(UploadJob).where(UploadJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        return None  # type: ignore

    job.status = UploadStatus.PROCESSING
    await db.flush()

    errors: list[dict[str, Any]] = []
    processed = 0
    failed = 0

    try:
        df = _read_csv_df(content)

        missing = REQUIRED_COLUMNS - set(df.columns)
        if missing:
            job.status = UploadStatus.FAILED
            job.error_summary = {
                "error": f"Missing required columns: {missing}",
                "detected_columns": list(df.columns),
            }
            job.completed_at = datetime.now(timezone.utc)
            await db.flush()
            return job

        total = len(df)
        job.total_records = total
        await db.flush()

        for idx, row in df.iterrows():
            try:
                code = str(row["legacy_material_code"]).strip()
                desc = str(row["original_description"]).strip()
                if not code or not desc:
                    raise ValueError("Empty code or description")

                # Use the shared NLP pipeline so uploads and matching apply
                # the same abbreviation and critical-attribute rules.
                from app.ai.pipeline import extract_attributes, normalize_description
                norm_desc = normalize_description(desc)

                mat = Material(
                    cpse_id=job.cpse_id,
                    legacy_material_code=code,
                    original_description=desc,
                    normalized_description=norm_desc,
                    unit_of_measure=str(row.get("unit_of_measure", "")).strip() or None,
                    manufacturer=str(row.get("manufacturer", "")).strip() or None,
                    status=MaterialStatus.ACTIVE,
                    upload_job_id=job.id,
                )
                db.add(mat)
                await db.flush()  # Flush to get mat.id

                # Generate and save embedding
                from app.services.embedding_service import generate_embedding
                emb_vec = generate_embedding(norm_desc)
                emb = MaterialEmbedding(
                    material_id=mat.id,
                    embedding=emb_vec,
                )
                db.add(emb)

                for attribute_name, attribute_value in extract_attributes(desc).items():
                    db.add(MaterialAttribute(
                        material_id=mat.id,
                        attribute_name=attribute_name,
                        attribute_value=attribute_value,
                        normalized_value=attribute_value,
                    ))

                processed += 1
            except Exception as e:
                failed += 1
                errors.append({"row": int(idx) + 2, "error": str(e)})  # +2: header + 0-index

        await db.flush()
        job.processed_records = processed
        job.failed_records = failed
        job.status = UploadStatus.COMPLETED if failed == 0 else UploadStatus.PARTIAL
        job.error_summary = {"errors": errors[:50]} if errors else None  # limit stored errors
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()

    except Exception as e:
        job.status = UploadStatus.FAILED
        job.error_summary = {"error": str(e)}
        job.completed_at = datetime.now(timezone.utc)
        await db.flush()

    return job
