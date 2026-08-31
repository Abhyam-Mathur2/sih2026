"""
SAP/ERP Integration API – mock endpoint for ERP system integration.

PS requirement: "Integration capability with SAP/ERP systems."

This endpoint accepts a material description (as an ERP system would send),
normalizes it, extracts attributes, and returns matching NMC recommendations.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.ai.pipeline import extract_attributes, normalize_description
from app.models.material import Material
from app.models.material_mapping import MaterialMapping, MappingStatus
from app.models.national_material import NationalMaterial
from app.models.user import User
from app.services.matching_engine import fuzzy_score, attribute_score

router = APIRouter()


class ERPLookupRequest(BaseModel):
    """Mimics a material record an ERP/SAP system would send."""
    material_description: str
    material_code: str | None = None
    unit_of_measure: str | None = None
    manufacturer: str | None = None
    cpse_code: str | None = None


class ERPLookupResponse(BaseModel):
    normalized_description: str
    extracted_attributes: dict[str, str]
    recommended_nmc: str | None = None
    nmc_description: str | None = None
    confidence: float = 0.0
    matching_materials: list[dict[str, Any]] = []


@router.post(
    "/lookup",
    response_model=ERPLookupResponse,
    summary="ERP/SAP material lookup – find matching National Material Code",
)
async def erp_lookup(
    payload: ERPLookupRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ERPLookupResponse:
    """
    Accepts a free-text material description (as SAP/ERP would send),
    normalizes it, extracts technical attributes, and returns the best
    matching National Material Code with confidence.
    """
    norm_desc = normalize_description(payload.material_description)
    attrs = extract_attributes(payload.material_description)

    # Find best matching NMC by comparing against all national materials
    nmc_result = await db.execute(select(NationalMaterial))
    nmcs = list(nmc_result.scalars().all())

    best_nmc = None
    best_score = 0.0

    for nmc in nmcs:
        fuz = fuzzy_score(norm_desc, nmc.standard_description)
        nmc_attrs = nmc.standard_attributes or {}
        att = attribute_score(attrs, nmc_attrs)
        combined = 0.6 * fuz + 0.4 * att
        if combined > best_score:
            best_score = combined
            best_nmc = nmc

    # Also find existing materials that match
    mat_result = await db.execute(
        select(Material)
        .options(selectinload(Material.mappings))
        .limit(200)
    )
    materials = list(mat_result.scalars().all())

    matching_materials = []
    for mat in materials:
        fuz = fuzzy_score(
            norm_desc,
            mat.normalized_description or mat.original_description,
        )
        if fuz >= 60.0:
            # Check if this material has an NMC mapping
            mapped_nmc = None
            for m in mat.mappings:
                if m.mapping_status == MappingStatus.APPROVED:
                    nmc_r = await db.execute(
                        select(NationalMaterial).where(
                            NationalMaterial.id == m.national_material_id
                        )
                    )
                    nm = nmc_r.scalar_one_or_none()
                    if nm:
                        mapped_nmc = nm.national_material_code
                    break

            matching_materials.append({
                "material_id": mat.id,
                "legacy_code": mat.legacy_material_code,
                "description": mat.original_description,
                "similarity": round(fuz, 1),
                "national_material_code": mapped_nmc,
            })

    matching_materials.sort(key=lambda x: x["similarity"], reverse=True)

    return ERPLookupResponse(
        normalized_description=norm_desc,
        extracted_attributes=attrs,
        recommended_nmc=best_nmc.national_material_code if best_nmc else None,
        nmc_description=best_nmc.standard_description if best_nmc else None,
        confidence=round(best_score, 1),
        matching_materials=matching_materials[:10],
    )


@router.post(
    "/export-mappings",
    response_model=list[dict[str, Any]],
    summary="Export all approved mappings for ERP import",
)
async def export_mappings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict[str, Any]]:
    """
    Returns all approved material→NMC mappings in a flat format
    suitable for import into SAP/ERP systems.
    """
    result = await db.execute(
        select(MaterialMapping)
        .where(MaterialMapping.mapping_status == MappingStatus.APPROVED)
        .options(
            selectinload(MaterialMapping.material),
            selectinload(MaterialMapping.national_material),
        )
    )
    mappings = list(result.scalars().all())

    return [
        {
            "material_id": m.material_id,
            "legacy_material_code": m.material.legacy_material_code if m.material else None,
            "original_description": m.material.original_description if m.material else None,
            "national_material_code": m.national_material.national_material_code if m.national_material else None,
            "standard_description": m.national_material.standard_description if m.national_material else None,
            "mapping_status": m.mapping_status.value,
            "approved_at": m.approved_at.isoformat() if m.approved_at else None,
        }
        for m in mappings
    ]
