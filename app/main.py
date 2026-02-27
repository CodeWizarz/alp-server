import logging
from fastapi import FastAPI
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting application in {settings.ENV} environment")


@app.get("/health")
def health_check():
    return {"status": "ok"}
