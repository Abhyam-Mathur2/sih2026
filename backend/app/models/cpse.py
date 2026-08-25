from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.material import Material
    from app.models.user import User


class CPSE(Base):
    """Central Public Sector Enterprise."""

    __tablename__ = "cpses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    materials: Mapped[list["Material"]] = relationship(
        "Material", back_populates="cpse", lazy="selectin"
    )
    users: Mapped[list["User"]] = relationship("User", back_populates="cpse", lazy="selectin")

    def __repr__(self) -> str:
        return f"<CPSE {self.short_code}: {self.name}>"
