"""Configurable, collision-safe National Material Code generation."""
from __future__ import annotations

import re
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.national_material import NationalMaterial

def _segment(value: str | None, fallback: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or fallback).upper())[:16] or fallback

async def generate_code(db: AsyncSession, category: str | None, attributes: dict[str, str]) -> str:
    """Generate NMC-CATEGORY-PRODUCT-MATERIAL-SIZE-SEQUENCE without reusing a code."""
    prefix = "-".join(["NMC", _segment(category, "GEN"), _segment(attributes.get("product_type"), "ITEM"), _segment(attributes.get("material_grade"), "NA"), _segment(attributes.get("size"), "NA")])
    count = (await db.execute(select(func.count()).select_from(NationalMaterial).where(NationalMaterial.national_material_code.like(f"{prefix}-%")))).scalar_one()
    return f"{prefix}-{count + 1:04d}"
