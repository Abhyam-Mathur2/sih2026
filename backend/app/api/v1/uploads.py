from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_cpse_manager
from app.db.session import get_db
from app.models.upload_job import UploadJob
from app.models.user import User
from app.schemas.upload import UploadJobRead
from app.services import upload_service

router = APIRouter()

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("", response_model=UploadJobRead, status_code=201, summary="Upload a CSV of materials")
async def upload_materials_csv(
    cpse_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_cpse_manager),
) -> UploadJob:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 50 MB")

    # Create upload job
    job = await upload_service.create_upload_job(
        db, cpse_id=cpse_id, file_name=file.filename, uploaded_by=current_user.id
    )
    try:
        job.storage_path = upload_service.store_original_csv(job.id, file.filename, content)
    except Exception as exc:
        # The CSV still goes through the established processing workflow; a
        # transient optional Storage outage must not discard user data.
        job.error_summary = {"storage_warning": str(exc)}

    # Process inline (for simplicity; in production, offload to a background task queue)
    job = await upload_service.process_csv_upload(db, job.id, content)
    return job


@router.get("/{job_id}", response_model=UploadJobRead, summary="Get upload job status")
async def get_upload_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> UploadJob:
    result = await db.execute(select(UploadJob).where(UploadJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail=f"Upload job {job_id} not found")
    return job


@router.get("", response_model=list[UploadJobRead], summary="List all upload jobs")
async def list_upload_jobs(
    cpse_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[UploadJob]:
    query = select(UploadJob)
    if cpse_id is not None:
        query = query.where(UploadJob.cpse_id == cpse_id)
    query = query.order_by(UploadJob.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
