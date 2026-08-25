from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.material_mapping import MappingStatus


class MappingCreate(BaseModel):
    material_id: int
    national_material_id: int


class MappingUpdate(BaseModel):
    mapping_status: MappingStatus


class MappingRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    material_id: int
    national_material_id: int
    mapping_status: MappingStatus
    approved_by: int | None
    approved_at: datetime | None
    created_at: datetime
