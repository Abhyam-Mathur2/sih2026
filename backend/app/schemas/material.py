from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.material import MaterialStatus


class MaterialAttributeRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    attribute_name: str
    attribute_value: str
    normalized_value: str | None
    confidence: float


class MaterialCreate(BaseModel):
    cpse_id: int
    legacy_material_code: str
    original_description: str
    category_id: int | None = None
    unit_of_measure: str | None = None
    manufacturer: str | None = None


class MaterialUpdate(BaseModel):
    normalized_description: str | None = None
    category_id: int | None = None
    unit_of_measure: str | None = None
    manufacturer: str | None = None
    status: MaterialStatus | None = None


class MaterialRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    cpse_id: int
    legacy_material_code: str
    original_description: str
    normalized_description: str | None
    category_id: int | None
    unit_of_measure: str | None
    manufacturer: str | None
    status: MaterialStatus
    upload_job_id: int | None
    created_at: datetime
    updated_at: datetime


class MaterialDetailRead(MaterialRead):
    model_config = {"from_attributes": True}

    attributes: list[MaterialAttributeRead] = []
