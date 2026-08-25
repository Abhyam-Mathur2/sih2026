from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.material import Material

# ---------------------------------------------------------------------------
# pgvector / local fallback detection
# ---------------------------------------------------------------------------
# When VECTOR_BACKEND=pgvector (default) and the pgvector Python package is
# installed, we use the proper Vector column type.
# When VECTOR_BACKEND=local (or pgvector package is absent), we fall back to
# storing the embedding as a JSON text column and do cosine similarity in Python.
# ---------------------------------------------------------------------------

_USE_PGVECTOR = False
try:
    if settings.vector_backend.lower() == "pgvector":
        from pgvector.sqlalchemy import Vector as _PgVector  # type: ignore
        _USE_PGVECTOR = True
except Exception:
    pass

PGVECTOR_ENABLED = _USE_PGVECTOR

if _USE_PGVECTOR:
    # -----------------------------------------------------------------------
    # pgvector-backed model
    # -----------------------------------------------------------------------
    from pgvector.sqlalchemy import Vector  # type: ignore

    class MaterialEmbedding(Base):
        """Stores the vector embedding (pgvector backend)."""

        __tablename__ = "material_embeddings"

        id: Mapped[int] = mapped_column(primary_key=True, index=True)
        material_id: Mapped[int] = mapped_column(
            Integer,
            ForeignKey("materials.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        )
        model_name: Mapped[str] = mapped_column(
            String(100), nullable=False, default=settings.embedding_model
        )
        embedding: Mapped[Any] = mapped_column(
            Vector(settings.embedding_dimension), nullable=True
        )
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

        # Relationships
        material: Mapped["Material"] = relationship("Material", back_populates="embeddings")

        def __repr__(self) -> str:
            return f"<MaterialEmbedding(pgvector) material_id={self.material_id}>"

else:
    # -----------------------------------------------------------------------
    # JSON/Text fallback – stores embedding as a JSON array string.
    # Cosine similarity is computed in Python (matching_engine.py).
    # -----------------------------------------------------------------------
    import json

    class MaterialEmbedding(Base):  # type: ignore[no-redef]
        """Stores the vector embedding (JSON text fallback – no pgvector required)."""

        __tablename__ = "material_embeddings"

        id: Mapped[int] = mapped_column(primary_key=True, index=True)
        material_id: Mapped[int] = mapped_column(
            Integer,
            ForeignKey("materials.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            index=True,
        )
        model_name: Mapped[str] = mapped_column(
            String(100), nullable=False, default=settings.embedding_model
        )
        # Stored as JSON text: "[0.1, 0.2, ...]"
        _embedding_json: Mapped[str | None] = mapped_column(
            "embedding", Text, nullable=True
        )
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )

        # Relationships
        material: Mapped["Material"] = relationship("Material", back_populates="embeddings")

        @property
        def embedding(self) -> list[float]:
            if self._embedding_json is None:
                return []
            try:
                return json.loads(self._embedding_json)
            except Exception:
                return []

        @embedding.setter
        def embedding(self, value: list[float]) -> None:
            self._embedding_json = json.dumps([float(x) for x in value])

        def __repr__(self) -> str:
            return f"<MaterialEmbedding(json) material_id={self.material_id}>"
