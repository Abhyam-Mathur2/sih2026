from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class CPSECreate(BaseModel):
    name: str
    short_code: str
    description: str | None = None


class CPSEUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CPSERead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    short_code: str
    description: str | None
    created_at: datetime
    updated_at: datetime
