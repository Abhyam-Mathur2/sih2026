from logging.config import fileConfig
import os
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import all models so Alembic can detect schema changes
from app.db.base import Base  # noqa: F401
import app.models  # noqa: F401

config = context.config
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# ------------------------------------------------------------------
# Database URL for Alembic (synchronous psycopg v3 driver)
# ------------------------------------------------------------------
# Priority:
#   1. DATABASE_URL_SYNC env var  (explicit sync URL, recommended)
#   2. DATABASE_URL env var       (async URL – driver prefix normalised below)
# There is intentionally no localhost fallback: the supported deployment uses
# a Supabase PostgreSQL project.
# ------------------------------------------------------------------
DATABASE_URL_SYNC = os.environ.get("DATABASE_URL_SYNC", "")

if not DATABASE_URL_SYNC:
    # Try to derive sync URL from DATABASE_URL by swapping asyncpg → psycopg
    async_url = os.environ.get("DATABASE_URL", "")
    if async_url:
        DATABASE_URL_SYNC = (
            async_url
            .replace("postgresql+asyncpg://", "postgresql+psycopg://")
            .replace("postgresql://", "postgresql+psycopg://")
        )

if not DATABASE_URL_SYNC:
    raise RuntimeError(
        "DATABASE_URL_SYNC (or DATABASE_URL) must be set in backend/.env. "
        "Use the Supabase Database connection string."
    )

config.set_main_option("sqlalchemy.url", DATABASE_URL_SYNC)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Supabase requires SSL; add connect_args when targeting supabase.co
    db_url = config.get_main_option("sqlalchemy.url")
    connect_args = {"sslmode": "require"} if "supabase.co" in db_url else {}

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
