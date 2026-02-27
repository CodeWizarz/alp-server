import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_database_url() -> str:
    """
    Ensure the DATABASE_URL uses the asyncpg driver prefix.
    Railway and most providers give a bare `postgresql://` URL —
    asyncpg requires `postgresql+asyncpg://`.
    """
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_db_url = _build_database_url()

# Log the host part only (mask credentials)
try:
    _host_part = _db_url.split("@")[1] if "@" in _db_url else _db_url
    logger.info(f"Database URL configured (host): {_host_part}")
except Exception:
    pass

engine = create_async_engine(
    _db_url,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    # Give more time on Railway cold starts
    connect_args={"timeout": 30},
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class DBStatus:
    is_ready: bool = False


db_status = DBStatus()


async def db_reconnect_task():
    """Background task: every 30 s retry the DB connection and update db_status."""
    while True:
        await asyncio.sleep(30)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            if not db_status.is_ready:
                db_status.is_ready = True
                logger.info("Database connection established/recovered in background")
        except Exception as e:
            if db_status.is_ready:
                db_status.is_ready = False
                logger.warning(f"Database connection lost in background check: {e}")
            else:
                # Still down — log details at DEBUG to avoid log spam
                logger.debug(f"Database still unreachable in background check: {e}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
