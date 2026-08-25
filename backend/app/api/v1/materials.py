from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_cpse_manager
from app.db.session import get_db
from app.models.material import MaterialStatus
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.material import MaterialCreate, MaterialDetailRead, MaterialRead, MaterialUpdate
from app.services import material_service
from app.services import match_service
from app.schemas.material_match import MatchRead

router = APIRouter()


@router.get("", response_model=PaginatedResponse[MaterialRead], summary="List materials with filters")
async def list_materials(
    cpse_id: int | None = Query(None),
    status: MaterialStatus | None = Query(None),
    category_id: int | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PaginatedResponse[MaterialRead]:
    skip = (page - 1) * size
    items, total = await material_service.list_materials(
        db, cpse_id=cpse_id, status=status, category_id=category_id, search=search, skip=skip, limit=size
    )
    return PaginatedResponse.create(
        items=[MaterialRead.model_validate(m) for m in items],
        total=total, page=page, size=size,
    )


@router.post("", response_model=MaterialRead, status_code=201, summary="Create a material")
async def create_material(
    payload: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_cpse_manager),
) -> MaterialRead:
    mat = await material_service.create_material(db, payload)
    return MaterialRead.model_validate(mat)


@router.get("/{material_id}", response_model=MaterialDetailRead, summary="Get material details")
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MaterialDetailRead:
    mat = await material_service.get_material(db, material_id)
    return MaterialDetailRead.model_validate(mat)


@router.patch("/{material_id}", response_model=MaterialRead, summary="Update a material")
async def update_material(
    material_id: int,
    payload: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_cpse_manager),
) -> MaterialRead:
    mat = await material_service.update_material(db, material_id, payload)
    return MaterialRead.model_validate(mat)


@router.delete("/{material_id}", status_code=204, summary="Delete a material")
async def delete_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_cpse_manager),
) -> None:
    await material_service.delete_material(db, material_id)

@router.post("/{material_id}/find-matches", response_model=list[MatchRead], summary="Run local hybrid AI matching")
async def find_matches(material_id: int, db: AsyncSession = Depends(get_db), _: User = Depends(require_cpse_manager)) -> list[MatchRead]:
    matches = await match_service.trigger_matching_for_material(db, material_id)
    return [MatchRead.model_validate(match) for match in matches]
