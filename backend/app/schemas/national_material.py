from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.national_material import NationalMaterialStatus


class NMCreate(BaseModel):
    national_material_code: str
    standard_description: str
    category_id: int | None = None
    standard_attributes: dict[str, Any] | None = None


class NMUpdate(BaseModel):
    standard_description: str | None = None
    category_id: int | None = None
    standard_attributes: dict[str, Any] | None = None
    status: NationalMaterialStatus | None = None


class NMRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    national_material_code: str
    standard_description: str
    category_id: int | None
    standard_attributes: dict[str, Any] | None
    status: NationalMaterialStatus
    created_at: datetime
    updated_at: datetime
