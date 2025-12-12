# app/models.py

from datetime import date

from sqlalchemy import String, Integer, Date, Text, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class GoalDB(Base):
    __tablename__ = "goals"

    goal_id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # basic info
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # numeric target and progress (e.g. kg, km, sessions)
    target_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "kg", "km", etc.

    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # e.g. "pending", "in_progress", "completed"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")

    def __repr__(self) -> str:
        return (
            f"<GoalDB(goal_id={self.goal_id}, user_id={self.user_id}, "
            f"title={self.title!r}, status={self.status!r})>"
        )
