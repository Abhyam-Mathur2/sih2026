"""
Material CRUD and query service.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.material import Material, MaterialStatus
from app.schemas.material import MaterialCreate, MaterialUpdate
from app.ai.pipeline import extract_attributes, normalize_description
from app.models.material_attribute import MaterialAttribute


async def get_material(db: AsyncSession, material_id: int) -> Material:
    result = await db.execute(
        select(Material)
        .where(Material.id == material_id)
        .options(selectinload(Material.attributes))
    )
    mat = result.scalar_one_or_none()
    if not mat:
        raise NotFoundError("Material", material_id)
    return mat


async def list_materials(
    db: AsyncSession,
    *,
    cpse_id: int | None = None,
    status: MaterialStatus | None = None,
    category_id: int | None = None,
    search: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Material], int]:
    """Return (items, total_count)."""
    query = select(Material)
    count_query = select(func.count()).select_from(Material)

    if cpse_id is not None:
        query = query.where(Material.cpse_id == cpse_id)
        count_query = count_query.where(Material.cpse_id == cpse_id)
    if status is not None:
        query = query.where(Material.status == status)
        count_query = count_query.where(Material.status == status)
    if category_id is not None:
        query = query.where(Material.category_id == category_id)
        count_query = count_query.where(Material.category_id == category_id)
    if search:
        pattern = f"%{search}%"
        search_filter = (
            Material.original_description.ilike(pattern)
            | Material.legacy_material_code.ilike(pattern)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    query = query.offset(skip).limit(limit).order_by(Material.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all()), total


async def create_material(db: AsyncSession, payload: MaterialCreate) -> Material:
    attrs = extract_attributes(payload.original_description)

    # Auto-classify if no category_id provided
    category_id = payload.category_id
    if not category_id:
        from app.services.classification_service import classify_material
        category_id = await classify_material(db, attrs.get("product_type"))

    mat = Material(
        cpse_id=payload.cpse_id,
        legacy_material_code=payload.legacy_material_code,
        original_description=payload.original_description,
        category_id=category_id,
        unit_of_measure=payload.unit_of_measure,
        manufacturer=payload.manufacturer,
        normalized_description=normalize_description(payload.original_description),
    )
    db.add(mat)
    await db.flush()
    for key, value in attrs.items():
        db.add(MaterialAttribute(material_id=mat.id, attribute_name=key, attribute_value=value, normalized_value=value))
    await db.flush()

    # Audit trail
    from app.services.audit_service import log_action
    await log_action(
        db,
        user_id=None,
        entity_type="Material",
        entity_id=mat.id,
        action="MATERIAL_CREATED",
        new_value={"code": mat.legacy_material_code, "description": mat.original_description},
    )

    await db.refresh(mat)
    return mat


async def update_material(
    db: AsyncSession, material_id: int, payload: MaterialUpdate
) -> Material:
    mat = await get_material(db, material_id)
    update_data = payload.model_dump(exclude_none=True)
    for field, value in update_data.items():
        setattr(mat, field, value)
    await db.flush()
    await db.refresh(mat)
    return mat


async def delete_material(db: AsyncSession, material_id: int) -> None:
    mat = await get_material(db, material_id)
    await db.delete(mat)
    await db.flush()
