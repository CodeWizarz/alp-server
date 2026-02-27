import asyncio
import logging
from typing import List
from fastapi import APIRouter, Header, HTTPException, status, Depends, Response
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
    db_event = ExecutionEvent(**event_in.model_dump())
    session.add(db_event)


async def ingestion_worker_task():
    while True:
        try:
            # Batch process events when DB is ready
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
                        # Push them back to the queue (simple retry logic)
                        for ev in batch:
                            await ingestion_queue.put(ev)
            elif batch and not db_status.is_ready:
                # DB still down, put them back
                for ev in batch:
                    await ingestion_queue.put(ev)

            # Wait a bit before checking queue again to avoid spinning if DB is down but queue has items
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

    for evt in events:
        await ingestion_queue.put(evt)

    logger.info(f"Queued {len(events)} events for tenant {tenant_id}")

    if not db_status.is_ready:
        response.headers["X-DB-Status"] = "disconnected"

    return {
        "status": "accepted",
        "queued": len(events),
        "db": "connected" if db_status.is_ready else "disconnected",
    }
