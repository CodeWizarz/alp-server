import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ExecutionEvent(Base):
    __tablename__ = "execution_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc)
    )
    event_type: Mapped[str] = mapped_column(String)
    payload: Mapped[dict] = mapped_column(JSONB)
    function_name: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str | None] = mapped_column(String, nullable=True)
