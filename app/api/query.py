import logging
from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, func, desc
from app.core.auth import verify_auth
from app.db.session import async_session_maker, db_status
from app.models.execution import ExecutionEvent
from app.schemas.query import QueryRequest, QueryResponse
from app.schemas.execution import ExecutionEventResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_events(
    request: QueryRequest, response: Response, tenant_id: str = Depends(verify_auth)
):
    # Debug: log the full incoming request so we can inspect what dashboard sends
    logger.info(
        f"Query request received from tenant={tenant_id}: {request.model_dump()}"
    )

    if not db_status.is_ready:
        response.headers["X-DB-Status"] = "disconnected"
        return QueryResponse(items=[], total=0)

    try:
        async with async_session_maker() as session:
            # tenant_id always comes from auth headers, not the request body
            query = select(ExecutionEvent).where(ExecutionEvent.tenant_id == tenant_id)

            # Structured filter fields
            if request.start_time:
                query = query.where(ExecutionEvent.timestamp >= request.start_time)
            if request.end_time:
                query = query.where(ExecutionEvent.timestamp <= request.end_time)
            if request.function_name:
                query = query.where(
                    ExecutionEvent.function_name == request.function_name
                )
            if request.status:
                query = query.where(ExecutionEvent.status == request.status)

            # Freeform query string: treat as a function_name partial match if
            # no structured filters are present (simple NL-style dashboard search)
            if request.query and not request.function_name and not request.status:
                query = query.where(
                    ExecutionEvent.function_name.ilike(f"%{request.query}%")
                )

            # Total count query for identical filter set
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total_count = total_result.scalar() or 0

            # Pagination & Ordering query
            query = query.order_by(desc(ExecutionEvent.timestamp))
            query = query.offset(request.offset).limit(request.limit)

            result = await session.execute(query)
            events = result.scalars().all()

            return QueryResponse(
                items=[ExecutionEventResponse.model_validate(e) for e in events],
                total=total_count,
            )
    except Exception as e:
        logger.error(f"Error querying events: {e}")
        response.headers["X-DB-Status"] = "error"
        return QueryResponse(items=[], total=0)
