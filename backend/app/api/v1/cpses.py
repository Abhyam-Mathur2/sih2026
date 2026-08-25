from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user, require_admin
from app.core.exceptions import ConflictError, NotFoundError
from app.db.session import get_db
from app.models.cpse import CPSE
from app.models.user import User
from app.schemas.cpse import CPSECreate, CPSERead, CPSEUpdate

router = APIRouter()


@router.get("", response_model=list[CPSERead], summary="List all CPSEs")
async def list_cpses(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[CPSE]:
    result = await db.execute(select(CPSE).order_by(CPSE.name))
    return list(result.scalars().all())


@router.post("", response_model=CPSERead, status_code=201, summary="Create a new CPSE (Admin only)")
async def create_cpse(
    payload: CPSECreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> CPSE:
    existing = await db.execute(select(CPSE).where(CPSE.short_code == payload.short_code.upper()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"CPSE '{payload.short_code}' already exists")
    cpse = CPSE(
        name=payload.name,
        short_code=payload.short_code.upper(),
        description=payload.description,
    )
    db.add(cpse)
    await db.flush()
    await db.refresh(cpse)
    return cpse


@router.get("/{cpse_id}", response_model=CPSERead, summary="Get CPSE by ID")
async def get_cpse(
    cpse_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CPSE:
    result = await db.execute(select(CPSE).where(CPSE.id == cpse_id))
    cpse = result.scalar_one_or_none()
    if not cpse:
        raise HTTPException(status_code=404, detail=f"CPSE {cpse_id} not found")
    return cpse


@router.patch("/{cpse_id}", response_model=CPSERead, summary="Update CPSE (Admin only)")
async def update_cpse(
    cpse_id: int,
    payload: CPSEUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> CPSE:
    result = await db.execute(select(CPSE).where(CPSE.id == cpse_id))
    cpse = result.scalar_one_or_none()
    if not cpse:
        raise HTTPException(status_code=404, detail=f"CPSE {cpse_id} not found")
    if payload.name:
        cpse.name = payload.name
    if payload.description is not None:
        cpse.description = payload.description
    await db.flush()
    await db.refresh(cpse)
    return cpse
