from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.material import Material


class MatchType(str, enum.Enum):
    IDENTICAL = "IDENTICAL"
    NEAR_DUPLICATE = "NEAR_DUPLICATE"
    FUNCTIONALLY_EQUIVALENT = "FUNCTIONALLY_EQUIVALENT"
    DIFFERENT = "DIFFERENT"


class MatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class MaterialMatch(Base):
    """AI-generated match between two materials, pending human review."""

    __tablename__ = "material_matches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=False, index=True
    )
    candidate_material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=False, index=True
    )

    # Score components (0–100)
    semantic_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fuzzy_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    attribute_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    technical_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    final_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)

    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType, name="matchtype"), nullable=False, index=True
    )
    status: Mapped[MatchStatus] = mapped_column(
        Enum(MatchStatus, name="matchstatus"),
        nullable=False,
        default=MatchStatus.PENDING,
        index=True,
    )

    # Explainability JSON
    explanation: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Reviewer info
    reviewed_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    reviewer_comment: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    source_material: Mapped["Material"] = relationship(
        "Material", foreign_keys=[source_material_id], back_populates="source_matches"
    )
    candidate_material: Mapped["Material"] = relationship(
        "Material", foreign_keys=[candidate_material_id], back_populates="candidate_matches"
    )

    def __repr__(self) -> str:
        return (
            f"<MaterialMatch {self.source_material_id}↔{self.candidate_material_id} "
            f"score={self.final_score:.1f} type={self.match_type}>"
        )
