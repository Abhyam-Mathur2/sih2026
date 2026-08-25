from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.national_material import NationalMaterial


class MappingStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class MaterialMapping(Base):
    """Maps a CPSE material to a National Material Code."""

    __tablename__ = "material_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("materials.id"), nullable=False, index=True
    )
    national_material_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("national_materials.id"), nullable=False, index=True
    )
    mapping_status: Mapped[MappingStatus] = mapped_column(
        Enum(MappingStatus, name="mappingstatus"),
        nullable=False,
        default=MappingStatus.PENDING,
        index=True,
    )
    approved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="mappings")
    national_material: Mapped["NationalMaterial"] = relationship(
        "NationalMaterial", back_populates="mappings"
    )

    def __repr__(self) -> str:
        return f"<MaterialMapping material={self.material_id} → nmc={self.national_material_id}>"
