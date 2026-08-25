from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class NationalMaterialStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"


class NationalMaterial(Base):
    """Unified National Material Code entry – the master record."""

    __tablename__ = "national_materials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    national_material_code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    standard_description: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("material_categories.id"), nullable=True, index=True
    )
    standard_attributes: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[NationalMaterialStatus] = mapped_column(
        Enum(NationalMaterialStatus, name="nationalmaterialstatus"),
        nullable=False,
        default=NationalMaterialStatus.ACTIVE,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    mappings: Mapped[list["MaterialMapping"]] = relationship(
        "MaterialMapping", back_populates="national_material"
    )

    def __repr__(self) -> str:
        return f"<NationalMaterial {self.national_material_code}>"
