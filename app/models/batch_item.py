import uuid

from sqlalchemy import (
String,
Integer,
ForeignKey,
Text,
DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.core.database import Base

class BatchItem(Base):
    __tablename__ = "batch_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id")
    )

    text: Mapped[str] = mapped_column(
        Text
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending"
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    result: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    processing_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    batch = relationship(
        "Batch",
        back_populates="items"
    )



