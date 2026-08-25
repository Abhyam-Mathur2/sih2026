from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UploadStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class UploadJob(Base):
    """Tracks a CSV bulk upload job."""

    __tablename__ = "upload_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cpse_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("cpses.id"), nullable=False, index=True
    )
    uploaded_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    # Object key in Supabase Storage (or local fallback path). The file is
    # never served from the frontend using backend credentials.
    storage_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, name="uploadstatus"),
        nullable=False,
        default=UploadStatus.PENDING,
        index=True,
    )
    error_summary: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<UploadJob #{self.id} {self.file_name} ({self.status})>"
