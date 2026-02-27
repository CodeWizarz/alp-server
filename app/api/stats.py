from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from app.core.auth import verify_auth
from app.db.session import async_session_maker
from app.models.execution import ExecutionEvent

router = APIRouter()


@router.get("/stats/errors")
async def get_error_stats(tenant_id: str = Depends(verify_auth)):
    async with async_session_maker() as session:
        # Count total events
        total_stmt = (
            select(func.count())
            .select_from(ExecutionEvent)
            .where(ExecutionEvent.tenant_id == tenant_id)
        )
        total_result = await session.execute(total_stmt)
        total_events = total_result.scalar() or 0

        # Count error events
        error_stmt = (
            select(func.count())
            .select_from(ExecutionEvent)
            .where(
                ExecutionEvent.tenant_id == tenant_id, ExecutionEvent.status == "error"
            )
        )
        error_result = await session.execute(error_stmt)
        error_events = error_result.scalar() or 0

        # Compute error rate
        error_rate = (error_events / total_events) if total_events > 0 else 0.0

        return {
            "total_events": total_events,
            "error_events": error_events,
            "error_rate": round(error_rate, 4),
        }


@router.get("/stats/top-functions")
async def get_top_functions(tenant_id: str = Depends(verify_auth)):
    async with async_session_maker() as session:
        stmt = (
            select(
                ExecutionEvent.function_name,
                func.count(ExecutionEvent.id).label("count"),
            )
            .where(ExecutionEvent.tenant_id == tenant_id)
            .where(ExecutionEvent.function_name.isnot(None))
            .group_by(ExecutionEvent.function_name)
            .order_by(desc("count"))
            .limit(10)
        )
        result = await session.execute(stmt)

        functions = []
        for row in result:
            functions.append({"function_name": row.function_name, "count": row.count})

        return functions
