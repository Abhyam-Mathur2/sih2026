from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.cpse import CPSE
from app.models.material import Material, MaterialStatus
from app.models.material_match import MatchStatus, MaterialMatch
from app.models.material_mapping import MappingStatus, MaterialMapping
from app.models.national_material import NationalMaterial
from app.models.user import User

router = APIRouter()


@router.get("", response_model=dict[str, Any], summary="Dashboard statistics")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict[str, Any]:
    # Total CPSEs
    cpse_count = (await db.execute(select(func.count()).select_from(CPSE))).scalar_one()

    # Total materials
    total_materials = (await db.execute(select(func.count()).select_from(Material))).scalar_one()

    # Materials by status
    mat_by_status_result = await db.execute(
        select(Material.status, func.count()).group_by(Material.status)
    )
    materials_by_status = {row[0].value: row[1] for row in mat_by_status_result.all()}

    # Pending matches
    pending_matches = (
        await db.execute(
            select(func.count()).select_from(MaterialMatch).where(
                MaterialMatch.status == MatchStatus.PENDING
            )
        )
    ).scalar_one()

    # Approved matches
    approved_matches = (
        await db.execute(
            select(func.count()).select_from(MaterialMatch).where(
                MaterialMatch.status == MatchStatus.APPROVED
            )
        )
    ).scalar_one()

    # Pending mappings
    pending_mappings = (
        await db.execute(
            select(func.count()).select_from(MaterialMapping).where(
                MaterialMapping.mapping_status == MappingStatus.PENDING
            )
        )
    ).scalar_one()

    # Approved mappings
    approved_mappings = (
        await db.execute(
            select(func.count()).select_from(MaterialMapping).where(
                MaterialMapping.mapping_status == MappingStatus.APPROVED
            )
        )
    ).scalar_one()

    # National materials count
    nm_count = (await db.execute(select(func.count()).select_from(NationalMaterial))).scalar_one()

    # Mapping completion rate
    total_mappings = pending_mappings + approved_mappings
    completion_rate = round(approved_mappings / total_mappings * 100, 1) if total_mappings > 0 else 0.0

    return {
        "cpses": cpse_count,
        "total_materials": total_materials,
        "materials_by_status": materials_by_status,
        "pending_matches": pending_matches,
        "approved_matches": approved_matches,
        "pending_mappings": pending_mappings,
        "approved_mappings": approved_mappings,
        "national_materials": nm_count,
        "mapping_completion_rate": completion_rate,
    }
