import asyncio
import logging
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Response
from app.core.auth import verify_auth
from app.schemas.execution import ExecutionEventCreate
from app.models.execution import ExecutionEvent
from app.db.session import async_session_maker, db_status

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory queue for graceful degradation
ingestion_queue = asyncio.Queue()

# Limit concurrent inserts to 10 to respect the connection pool bounds (pool=5, max_overflow=10)
CONN_SEMAPHORE = asyncio.Semaphore(10)


async def _insert_single_event_with_session(event_in: ExecutionEventCreate, session):
    data = event_in.model_dump()
    # Ensure tenant_id is always set (stamped from auth headers upstream)
    db_event = ExecutionEvent(**data)
    session.add(db_event)


async def ingestion_worker_task():
    while True:
        try:
            batch = []
            while not ingestion_queue.empty() and len(batch) < 100:
                batch.append(await ingestion_queue.get())

            if batch and db_status.is_ready:
                async with CONN_SEMAPHORE:
                    try:
                        async with async_session_maker() as session:
                            for event_in in batch:
                                await _insert_single_event_with_session(
                                    event_in, session
                                )
                            await session.commit()
                            logger.info(
                                f"Background worker flushed {len(batch)} events to DB"
                            )
                    except Exception as e:
                        logger.error(f"Background worker failed to flush events: {e}")
                        for ev in batch:
                            await ingestion_queue.put(ev)
            elif batch and not db_status.is_ready:
                for ev in batch:
                    await ingestion_queue.put(ev)

            await asyncio.sleep(1)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in ingestion worker: {e}")
            await asyncio.sleep(5)


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_events(
    events: List[ExecutionEventCreate],
    response: Response,
    tenant_id: str = Depends(verify_auth),
):
    if len(events) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 events per request")

    from datetime import datetime, timezone

    for evt in events:
        # Stamp tenant_id and timestamp server-side if client omitted them
        if not evt.tenant_id:
            evt.tenant_id = tenant_id
        if not evt.timestamp:
            evt.timestamp = datetime.now(timezone.utc)
        await ingestion_queue.put(evt)

    logger.info(f"Queued {len(events)} events for tenant {tenant_id}")

    if not db_status.is_ready:
        response.headers["X-DB-Status"] = "disconnected"

    return {
        "status": "accepted",
        "queued": len(events),
        "db": "connected" if db_status.is_ready else "disconnected",
    }
