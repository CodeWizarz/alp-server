import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from app.api.ingest import router as ingest_router
from app.db.base import Base
import app.models.execution  # Import models to ensure they align with Base

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

db_ready = False


async def db_reconnect_task():
    global db_ready
    while True:
        await asyncio.sleep(30)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                if not db_ready:
                    db_ready = True
                    logger.info(
                        "Database connection established/recovered in background"
                    )
        except Exception:
            if db_ready:
                db_ready = False
                logger.warning("Database connection lost in background check")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_ready
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("SELECT 1"))
            db_ready = True
            logger.info("Database connection successful on startup and tables verified")
    except Exception as e:
        logger.warning(f"Database connection failed on startup: {e}")
        db_ready = False

    task = asyncio.create_task(db_reconnect_task())
    yield
    task.cancel()
    await engine.dispose()
    logger.info("Database engine disposed")


from app.api.auth_test import router as auth_test_router
from app.api.stats import router as stats_router
from app.api.query import router as query_router

app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(ingest_router, prefix="/v1")
app.include_router(auth_test_router, prefix="/v1")
app.include_router(stats_router, prefix="/v1")
app.include_router(query_router, prefix="/v1")


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting application in {settings.ENV} environment")


@app.get("/health")
def health_check():
    return {"status": "ok", "db": "connected" if db_ready else "disconnected"}
