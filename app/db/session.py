import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_async_engine(
    settings.DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class DBStatus:
    is_ready: bool = False


db_status = DBStatus()


async def db_reconnect_task():
    while True:
        await asyncio.sleep(30)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                if not db_status.is_ready:
                    db_status.is_ready = True
                    logger.info(
                        "Database connection established/recovered in background"
                    )
        except Exception:
            if db_status.is_ready:
                db_status.is_ready = False
                logger.warning("Database connection lost in background check")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
