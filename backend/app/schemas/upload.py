from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.upload_job import UploadStatus


class UploadJobRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    cpse_id: int
    uploaded_by: int | None
    file_name: str
    storage_path: str | None
    total_records: int
    processed_records: int
    failed_records: int
    status: UploadStatus
    error_summary: dict[str, Any] | None
    created_at: datetime
    completed_at: datetime | None
