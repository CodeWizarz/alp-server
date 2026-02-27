import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine, db_status, db_reconnect_task
from app.api.ingest import router as ingest_router, ingestion_worker_task
from app.api.auth_test import router as auth_test_router
from app.api.stats import router as stats_router
from app.api.query import router as query_router
from app.db.base import Base
import app.models.execution  # Import models to ensure they align with Base

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("SELECT 1"))
            db_status.is_ready = True
            logger.info("Database connection successful on startup and tables verified")
    except Exception as e:
        logger.warning(f"Database connection failed on startup: {e}")
        db_status.is_ready = False

    reconnect_task = asyncio.create_task(db_reconnect_task())
    queue_worker_task = asyncio.create_task(ingestion_worker_task())
    yield
    reconnect_task.cancel()
    queue_worker_task.cancel()
    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router, prefix="/v1")
app.include_router(auth_test_router, prefix="/v1")
app.include_router(stats_router, prefix="/v1")
app.include_router(query_router, prefix="/v1")


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting application in {settings.ENV} environment")


@app.get("/health")
def health_check():
    return {"status": "ok", "db": "connected" if db_status.is_ready else "disconnected"}
