from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for ORM models."""


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))  # 1..200 chars
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    # Metadata fields
    priority: Mapped[str] = mapped_column(
        String(10), default="medium"
    )  # low|medium|high
    # Optional due date; stored as DATE (NULL allowed)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)
    # Timezone-aware UTC timestamp (set on insert by ORM default)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    def __init__(
        self,
        title: str,
        done: bool = False,
        priority: str = "medium",
        due_date: date | None = None,
    ) -> None:
        self.title = title
        self.done = done
        self.priority = priority
        self.due_date = due_date
