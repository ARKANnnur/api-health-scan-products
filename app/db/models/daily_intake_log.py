from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import (
    ConsumptionType,
    ContainerSize,
    ContainerType,
    MeasurementType,
)


class DailyIntakeLog(Base):
    __tablename__ = "daily_intake_logs"

    __table_args__ = (
        CheckConstraint(
            "portion_consumed_amount > 0 AND portion_consumed_amount <= 10000",
            name="daily_intake_logs_portion_amount_check",
        ),
        CheckConstraint(
            "portion_servings IS NULL OR " "(portion_servings > 0 AND portion_servings <= 5)",
            name="daily_intake_logs_portion_servings_check",
        ),
        CheckConstraint(
            "input_method IS NULL OR "
            "input_method IN ('preset', 'custom', 'estimate', 'serving_size')",
            name="daily_intake_logs_input_method_check",
        ),
        Index("idx_daily_intake_logs_user_id", "user_id"),
        Index(
            "idx_daily_intake_logs_logged_at",
            text("logged_at DESC"),
        ),
        Index(
            "idx_daily_intake_logs_user_logged",
            "user_id",
            text("logged_at DESC"),
        ),
        Index("idx_daily_intake_logs_product_id", "product_id"),
        Index(
            "idx_daily_intake_logs_is_synced",
            "is_synced",
            postgresql_where=text("is_synced = false"),
        ),
        Index(
            "idx_daily_intake_logs_device_id",
            "device_id",
            postgresql_where=text("device_id IS NOT NULL"),
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
    product_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("scanned_products.id", ondelete="RESTRICT"),
    )

    consumption_type: Mapped[ConsumptionType] = mapped_column(
        Enum(ConsumptionType, name="consumption_type", create_type=False),
    )

    portion_consumed_amount: Mapped[Decimal] = mapped_column(Numeric(8, 2))

    portion_servings: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    measurement_type: Mapped[MeasurementType | None] = mapped_column(
        Enum(MeasurementType, name="measurement_type", create_type=False),
    )
    container_type: Mapped[ContainerType | None] = mapped_column(
        Enum(ContainerType, name="container_type", create_type=False),
    )
    container_size: Mapped[ContainerSize | None] = mapped_column(
        Enum(ContainerSize, name="container_size", create_type=False),
    )
    input_method: Mapped[str | None] = mapped_column(String)
    estimated: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
    )

    calories_kcal: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    saturated_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    caffeine_mg: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    client_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    device_id: Mapped[str | None] = mapped_column(Text)
    is_synced: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("true"),
    )
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
