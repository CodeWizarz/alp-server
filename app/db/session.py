import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_database_url() -> Optional[str]:
    """
    Ensure the DATABASE_URL uses the asyncpg driver prefix.
    Railway provides bare `postgresql://` — asyncpg requires `postgresql+asyncpg://`.
    Returns None if DATABASE_URL is not configured.
    """
    url = settings.DATABASE_URL
    if not url:
        logger.error(
            "DATABASE_URL environment variable is not set — DB will be unavailable"
        )
        return None
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_db_url = _build_database_url()

# Log the host part only (mask credentials) for Railway log visibility
if _db_url:
    try:
        _host_part = _db_url.split("@")[1] if "@" in _db_url else _db_url
        logger.info(f"Database URL configured — connecting to: {_host_part}")
    except Exception:
        pass
else:
    logger.error("No DATABASE_URL — all DB operations will be skipped")

engine = create_async_engine(
    _db_url
    or "postgresql+asyncpg://invalid/invalid",  # placeholder to avoid import crash
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    connect_args={"timeout": 30},  # give Railway cold starts extra time
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class DBStatus:
    is_ready: bool = False


db_status = DBStatus()


async def db_reconnect_task():
    """
    Background task: retry DB connection with progressive backoff.
    First 5 retries every 10s, then every 30s. Always logs at WARNING so
    Railway logs make failures clearly visible.
    """
    retry_count = 0
    while True:
        interval = 10 if retry_count < 5 else 30
        await asyncio.sleep(interval)
        retry_count += 1

        if not _db_url:
            logger.error("Skipping DB reconnect — DATABASE_URL not set")
            continue

        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            if not db_status.is_ready:
                db_status.is_ready = True
                retry_count = 0  # reset on success
                logger.info("Database connection established/recovered in background")
        except Exception as e:
            if db_status.is_ready:
                db_status.is_ready = False
                logger.warning(f"Database connection lost: {type(e).__name__}: {e}")
            else:
                # Log every attempt at WARNING so Railway logs surface the root cause
                logger.warning(
                    f"Database still unreachable (attempt {retry_count}): "
                    f"{type(e).__name__}: {e}"
                )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
