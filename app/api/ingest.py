import asyncio
import logging
from typing import List
from fastapi import APIRouter, Header, HTTPException, status, Depends
from app.core.auth import verify_auth
from app.schemas.execution import ExecutionEventCreate
from app.models.execution import ExecutionEvent
from app.db.session import async_session_maker

logger = logging.getLogger(__name__)

router = APIRouter()

# Limit concurrent inserts to 10 to respect the connection pool bounds (pool=5, max_overflow=10)
CONN_SEMAPHORE = asyncio.Semaphore(10)


async def _insert_single_event(event_in: ExecutionEventCreate):
    async with CONN_SEMAPHORE:
        async with async_session_maker() as session:
            db_event = ExecutionEvent(**event_in.model_dump())
            session.add(db_event)
            await session.commit()


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    events: List[ExecutionEventCreate], tenant_id: str = Depends(verify_auth)
):
    if len(events) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 events per request")

    logger.info(f"Received {len(events)} events for tenant {tenant_id}")

    tasks = [_insert_single_event(evt) for evt in events]
    # Gather exceptions if insert fails, but allowing successful ones to pass isn't fully required, gather is enough
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Check if any tasks failed to log
    failed = [res for res in results if isinstance(res, Exception)]
    if failed:
        logger.error(
            f"Failed to insert some events: {len(failed)} errors. First error: {failed[0]}"
        )
        # Consider handling full failure vs partial success; for now, log and return 202

    return {
        "status": "accepted",
        "ingested": len(events) - len(failed),
        "errors": len(failed),
    }
