from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_reviewer
from app.db.session import get_db
from app.models.material_mapping import MappingStatus, MaterialMapping
from app.models.user import User
from app.schemas.material_mapping import MappingCreate, MappingRead, MappingUpdate

router = APIRouter()


@router.get("", response_model=list[MappingRead], summary="List material mappings")
async def list_mappings(
    material_id: int | None = None,
    status: MappingStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MaterialMapping]:
    query = select(MaterialMapping)
    if material_id is not None:
        query = query.where(MaterialMapping.material_id == material_id)
    if status is not None:
        query = query.where(MaterialMapping.mapping_status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=MappingRead, status_code=201, summary="Create a mapping")
async def create_mapping(
    payload: MappingCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_reviewer),
) -> MaterialMapping:
    mapping = MaterialMapping(
        material_id=payload.material_id,
        national_material_id=payload.national_material_id,
        mapping_status=MappingStatus.PENDING,
    )
    db.add(mapping)
    await db.flush()
    await db.refresh(mapping)
    return mapping


@router.patch("/{mapping_id}", response_model=MappingRead, summary="Approve or reject a mapping")
async def update_mapping(
    mapping_id: int,
    payload: MappingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> MaterialMapping:
    result = await db.execute(select(MaterialMapping).where(MaterialMapping.id == mapping_id))
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(status_code=404, detail=f"Mapping {mapping_id} not found")
    mapping.mapping_status = payload.mapping_status
    if payload.mapping_status == MappingStatus.APPROVED:
        mapping.approved_by = current_user.id
        mapping.approved_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(mapping)
    return mapping
