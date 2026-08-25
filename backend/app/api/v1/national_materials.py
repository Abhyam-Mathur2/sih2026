from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models.national_material import NationalMaterial, NationalMaterialStatus
from app.models.user import User
from app.schemas.national_material import NMCreate, NMRead, NMUpdate

router = APIRouter()


@router.get("", response_model=list[NMRead], summary="List national materials")
async def list_national_materials(
    status: NationalMaterialStatus | None = Query(None),
    category_id: int | None = Query(None),
    search: str | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[NationalMaterial]:
    query = select(NationalMaterial)
    if status:
        query = query.where(NationalMaterial.status == status)
    if category_id:
        query = query.where(NationalMaterial.category_id == category_id)
    if search:
        query = query.where(NationalMaterial.standard_description.ilike(f"%{search}%"))
    query = query.offset(skip).limit(limit).order_by(NationalMaterial.national_material_code)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=NMRead, status_code=201, summary="Create a national material (Admin only)")
async def create_national_material(
    payload: NMCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> NationalMaterial:
    nm = NationalMaterial(
        national_material_code=payload.national_material_code,
        standard_description=payload.standard_description,
        category_id=payload.category_id,
        standard_attributes=payload.standard_attributes,
    )
    db.add(nm)
    await db.flush()
    await db.refresh(nm)
    return nm


@router.get("/{nm_id}", response_model=NMRead, summary="Get national material by ID")
async def get_national_material(
    nm_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> NationalMaterial:
    result = await db.execute(select(NationalMaterial).where(NationalMaterial.id == nm_id))
    nm = result.scalar_one_or_none()
    if not nm:
        raise HTTPException(status_code=404, detail=f"National Material {nm_id} not found")
    return nm


@router.patch("/{nm_id}", response_model=NMRead, summary="Update a national material (Admin only)")
async def update_national_material(
    nm_id: int,
    payload: NMUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> NationalMaterial:
    result = await db.execute(select(NationalMaterial).where(NationalMaterial.id == nm_id))
    nm = result.scalar_one_or_none()
    if not nm:
        raise HTTPException(status_code=404, detail=f"National Material {nm_id} not found")
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(nm, field, value)
    await db.flush()
    await db.refresh(nm)
    return nm
