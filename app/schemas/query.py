from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.execution import ExecutionEventResponse


class QueryRequest(BaseModel):
    # Allow (and ignore) any extra fields the dashboard may send
    model_config = ConfigDict(extra="ignore")

    # Freeform query string from simple dashboard requests like {"query": "..."}
    query: Optional[str] = None

    # Structured filter fields (all optional)
    tenant_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    function_name: Optional[str] = None
    status: Optional[str] = None
    limit: int = 50
    offset: int = 0


class QueryResponse(BaseModel):
    items: List[ExecutionEventResponse]
    total: int
