import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict


class ExecutionEventCreate(BaseModel):
    # tenant_id comes from X-Tenant-ID auth header — body may omit it
    tenant_id: Optional[str] = None
    event_type: str
    payload: dict[str, Any]
    timestamp: Optional[datetime] = (
        None  # server sets this from model default if absent
    )
    function_name: Optional[str] = None
    latency_ms: Optional[int] = None
    status: Optional[str] = None


class ExecutionEventResponse(BaseModel):
    id: uuid.UUID
    tenant_id: str
    timestamp: datetime
    event_type: str
    payload: dict[str, Any]
    function_name: Optional[str] = None
    latency_ms: Optional[int] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
