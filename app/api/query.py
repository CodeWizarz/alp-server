from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from app.core.auth import verify_auth
from app.db.session import async_session_maker
from app.models.execution import ExecutionEvent
from app.schemas.query import QueryRequest, QueryResponse
from app.schemas.execution import ExecutionEventResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_events(request: QueryRequest, tenant_id: str = Depends(verify_auth)):
    async with async_session_maker() as session:
        # Base query combining filters
        query = select(ExecutionEvent).where(ExecutionEvent.tenant_id == tenant_id)

        if request.start_time:
            query = query.where(ExecutionEvent.timestamp >= request.start_time)
        if request.end_time:
            query = query.where(ExecutionEvent.timestamp <= request.end_time)
        if request.function_name:
            query = query.where(ExecutionEvent.function_name == request.function_name)
        if request.status:
            query = query.where(ExecutionEvent.status == request.status)

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
