"""
Audit service – records every significant action for governance traceability.

Every match review, mapping approval, material creation/update, NMC generation,
and bulk upload is logged as an immutable AuditLog row.  This is a **named**
requirement in the SIH PS ("Audit trail and governance mechanism").
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    *,
    user_id: int | None,
    entity_type: str,
    entity_id: str | int,
    action: str,
    old_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create an immutable audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        old_value=old_value,
        new_value=new_value,
        extra_metadata=metadata,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    return entry
