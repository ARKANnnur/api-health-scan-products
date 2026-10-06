from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyLimit(Base):
    __tablename__ = "daily_limits"

    __table_args__ = (
        Index("idx_daily_limits_user_id", "user_id"),
        Index(
            "idx_daily_limits_computed_at",
            text("computed_at DESC"),
        ),
        Index(
            "idx_daily_limits_computation_version",
            "computation_version",
        ),
        # UNIQUE partial index — hanya satu active limit per user
        Index(
            "idx_daily_limits_user_active_unique",
            "user_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("profiles.id", ondelete="CASCADE"),
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    bmr_kcal: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    tdee_kcal: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    calories_kcal: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    sugar_g: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    caffeine_mg: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    sodium_mg: Mapped[Decimal] = mapped_column(Numeric(7, 2))
    saturated_fat_g: Mapped[Decimal] = mapped_column(Numeric(6, 2))

    reference_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    reference_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String))
    warnings: Mapped[list[Any]] = mapped_column(
        JSONB,
        server_default=text("'[]'::jsonb"),
    )

    computation_version: Mapped[str | None] = mapped_column(String)
    algorithm_hash: Mapped[str | None] = mapped_column(String)

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
    )
