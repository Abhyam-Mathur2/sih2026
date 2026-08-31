from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_cache_dir() -> str:
    """
    Cross-platform Sentence Transformer model cache directory.
    Resolves to ~/.bmim_cache on all platforms.
    Override with MODEL_CACHE_DIR env var.
    """
    return str(Path.home() / ".bmim_cache")


def _default_upload_dir() -> str:
    """
    Cross-platform fallback upload directory (used when STORAGE_BACKEND=local).
    Uses the OS temp folder so it always exists and is writable.
    Override with UPLOAD_DIR env var.
    """
    return str(Path(tempfile.gettempdir()) / "bmim_uploads")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "SANGAM – Standardized AI-driven National Gateway for Aggregated Materials"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # ------------------------------------------------------------------
    # Database (Supabase PostgreSQL)
    # ------------------------------------------------------------------
    # Provide DATABASE_URL and DATABASE_URL_SYNC directly in .env.  BMIM
    # deliberately has no localhost PostgreSQL fallback: a Supabase project
    # is the only database prerequisite for the supported setup.
    database_url: str = ""
    database_url_sync: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_async_db_url(cls, v: str, info: Any) -> str:
        if v:
            # Normalise driver prefix for asyncpg
            # psycopg URLs coming from Supabase dashboard should still work
            if v.startswith("postgresql://") and "+asyncpg" not in v and "+psycopg" not in v:
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            return v
        return ""

    @field_validator("database_url_sync", mode="before")
    @classmethod
    def assemble_sync_db_url(cls, v: str, info: Any) -> str:
        if v:
            # Normalise for psycopg v3 sync driver used by Alembic
            if v.startswith("postgresql://") and "+psycopg" not in v and "+asyncpg" not in v:
                v = v.replace("postgresql://", "postgresql+psycopg://", 1)
            return v
        async_url = info.data.get("database_url", "")
        return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

    # ------------------------------------------------------------------
    # Supabase
    # ------------------------------------------------------------------
    # Found in: Supabase Dashboard → Project Settings → API
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "material-uploads"

    # ------------------------------------------------------------------
    # Security / JWT
    # ------------------------------------------------------------------
    # JWT_SECRET_KEY is accepted as the explicit name. SECRET_KEY remains
    # supported for existing deployments.
    secret_key: str = "change-this-to-a-long-random-secret-key"
    jwt_secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ------------------------------------------------------------------
    # CORS
    # ------------------------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ------------------------------------------------------------------
    # AI / Matching Engine
    # ------------------------------------------------------------------
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    candidate_top_k: int = 20
    model_cache_dir: str = _default_cache_dir()

    weight_semantic: float = 0.35
    weight_fuzzy: float = 0.20
    weight_attribute: float = 0.25
    weight_technical: float = 0.20

    threshold_identical: float = 95.0
    threshold_near_duplicate: float = 80.0
    threshold_functional: float = 60.0

    # ------------------------------------------------------------------
    # Vector backend
    # ------------------------------------------------------------------
    # pgvector  – use PostgreSQL pgvector extension (Supabase default, recommended)
    # local     – Python/numpy cosine similarity (no DB extension needed)
    vector_backend: str = "pgvector"

    # ------------------------------------------------------------------
    # Storage backend
    # ------------------------------------------------------------------
    # supabase – upload CSVs to Supabase Storage (recommended)
    # local    – save files to local filesystem (fallback / offline dev)
    storage_backend: str = "supabase"

    # Local fallback directory (used when storage_backend=local)
    max_upload_size_mb: int = 50
    upload_dir: str = _default_upload_dir()


settings = Settings()

# Preserve the existing SECRET_KEY setting while allowing the clearer
# JWT_SECRET_KEY requested by the Supabase setup guide.
if settings.jwt_secret_key:
    settings.secret_key = settings.jwt_secret_key
