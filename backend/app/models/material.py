from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.cpse import CPSE
    from app.models.material_category import MaterialCategory
    from app.models.material_attribute import MaterialAttribute
    from app.models.material_embedding import MaterialEmbedding
    from app.models.material_match import MaterialMatch
    from app.models.material_mapping import MaterialMapping


class MaterialStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    PENDING_REVIEW = "PENDING_REVIEW"
    MAPPED = "MAPPED"
    REJECTED = "REJECTED"


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cpse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cpses.id"), nullable=False, index=True
    )
    legacy_material_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    original_description: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("material_categories.id"), nullable=True, index=True
    )
    unit_of_measure: Mapped[str | None] = mapped_column(String(50), nullable=True)
    manufacturer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[MaterialStatus] = mapped_column(
        Enum(MaterialStatus, name="materialstatus"),
        nullable=False,
        default=MaterialStatus.ACTIVE,
        index=True,
    )
    upload_job_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("upload_jobs.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    cpse: Mapped["CPSE"] = relationship("CPSE", back_populates="materials")
    category: Mapped["MaterialCategory | None"] = relationship(
        "MaterialCategory", back_populates="materials"
    )
    attributes: Mapped[list["MaterialAttribute"]] = relationship(
        "MaterialAttribute", back_populates="material", cascade="all, delete-orphan"
    )
    embeddings: Mapped[list["MaterialEmbedding"]] = relationship(
        "MaterialEmbedding", back_populates="material", cascade="all, delete-orphan"
    )
    source_matches: Mapped[list["MaterialMatch"]] = relationship(
        "MaterialMatch",
        foreign_keys="MaterialMatch.source_material_id",
        back_populates="source_material",
    )
    candidate_matches: Mapped[list["MaterialMatch"]] = relationship(
        "MaterialMatch",
        foreign_keys="MaterialMatch.candidate_material_id",
        back_populates="candidate_material",
    )
    mappings: Mapped[list["MaterialMapping"]] = relationship(
        "MaterialMapping", back_populates="material"
    )

    def __repr__(self) -> str:
        return f"<Material {self.legacy_material_code}: {self.original_description[:50]}>"
