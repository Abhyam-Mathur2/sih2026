from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.material_match import MatchStatus, MatchType
from app.schemas.material import MaterialRead


class MatchRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    source_material_id: int
    candidate_material_id: int
    semantic_score: float
    fuzzy_score: float
    attribute_score: float
    technical_score: float
    final_score: float
    match_type: MatchType
    status: MatchStatus
    explanation: dict[str, Any] | None
    reviewed_by: int | None
    reviewer_comment: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MatchDetailRead(MatchRead):
    model_config = {"from_attributes": True}

    source_material: MaterialRead | None = None
    candidate_material: MaterialRead | None = None


class MatchReview(BaseModel):
    action: MatchStatus  # APPROVED or REJECTED or MODIFIED
    reviewer_comment: str | None = None
    modified_score: float | None = None  # if action is MODIFIED


class TriggerMatchRequest(BaseModel):
    material_id: int
    top_k: int = 20
