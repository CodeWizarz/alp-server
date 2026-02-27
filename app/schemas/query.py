from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.execution import ExecutionEventResponse


class QueryRequest(BaseModel):
    tenant_id: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    function_name: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


class QueryResponse(BaseModel):
    items: List[ExecutionEventResponse]
    total: int
