from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

if not settings.database_url:
    raise RuntimeError(
        "DATABASE_URL is required. Configure backend/.env with the Supabase "
        "PostgreSQL connection string before starting BMIM."
    )

# ------------------------------------------------------------------
# Engine configuration tuned for Supabase (cloud PostgreSQL).
#
# pool_size / max_overflow:
#   Supabase free tier allows ~20 simultaneous direct connections.
#   Keep pool small to stay well within limits.
#
# pool_pre_ping=True:
#   Validates connections before use; important for cloud DBs where
#   idle connections may be dropped by firewalls/proxies.
#
# pool_recycle=300:
#   Recycle connections every 5 minutes to avoid stale connections.
# ------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
    connect_args={
        # Supabase requires SSL; asyncpg handles it automatically for
        # supabase.co hosts. Explicit ssl="require" ensures it works
        # even when the URL doesn't include sslmode.
        "ssl": "require",
    } if "supabase.co" in settings.database_url else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency – yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
