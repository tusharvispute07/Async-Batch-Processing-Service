import uuid

from sqlalchemy import (
String,
Integer,
DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    mapped_column,
    Mapped,
    relationship
)
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

class Batch(Base):
    __tablename__ = "batches"


    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    tenant_id: Mapped[str] = mapped_column(
        String,
        index=True
    )

    idempotency_key: Mapped[str] = mapped_column(
        String,
        index=True
    )

    payload_hash: Mapped[str] = mapped_column(
        String
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending"
    )

    total: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    done: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    failed: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    items = relationship(
        "BatchItem",
        back_populates="batch"
    )
