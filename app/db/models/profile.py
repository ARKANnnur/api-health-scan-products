from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import AgeGroup


class Profile(Base):
    __tablename__ = "profiles"

    __table_args__ = (
        CheckConstraint(
            "age_years >= 7 AND age_years <= 120",
            name="profiles_age_years_check",
        ),
        CheckConstraint(
            "weight_kg >= 5 AND weight_kg <= 300",
            name="profiles_weight_kg_check",
        ),
        CheckConstraint(
            "height_cm >= 50 AND height_cm <= 250",
            name="profiles_height_cm_check",
        ),
        CheckConstraint(
            "gender IN ('MALE', 'FEMALE')",
            name="profiles_gender_check",
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    age_years: Mapped[int] = mapped_column(Integer)
    age_group: Mapped[AgeGroup] = mapped_column(
        Enum(AgeGroup, name="age_group", create_type=False),
    )
    gender: Mapped[str] = mapped_column(String)
    weight_kg: Mapped[float] = mapped_column(Numeric(5, 2))
    height_cm: Mapped[float] = mapped_column(Numeric(5, 2))

    is_minor: Mapped[bool] = mapped_column(
        Boolean,
        Computed("age_years < 18", persisted=True),
    )

    disclaimer_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    disclaimer_version: Mapped[str | None] = mapped_column(String)
    profile_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deletion_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )