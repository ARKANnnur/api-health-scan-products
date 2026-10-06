from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.enums import ContainerSize, ContainerType, MeasurementType


class PortionReference(Base):
    __tablename__ = "portion_references"

    __table_args__ = (
        CheckConstraint(
            "(amount_gram IS NOT NULL AND amount_gram > 0) "
            "OR (amount_ml IS NOT NULL AND amount_ml > 0)",
            name="portion_ref_amount_check",
        ),
        CheckConstraint(
            "(measurement_type = 'CONTAINER' AND container_type IS NOT NULL) "
            "OR measurement_type != 'CONTAINER'",
            name="portion_ref_container_check",
        ),
        Index("idx_portion_references_name", "name"),
        Index("idx_portion_references_reference_id", "reference_id"),
        Index("idx_portion_references_category", "category"),
        Index("idx_portion_references_measurement", "measurement_type"),
        Index(
            "idx_portion_references_container",
            "container_type",
            "container_size",
            postgresql_where=text("container_type IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    name: Mapped[str] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String)

    measurement_type: Mapped[MeasurementType] = mapped_column(
        Enum(MeasurementType, name="measurement_type", create_type=False),
    )
    container_type: Mapped[ContainerType | None] = mapped_column(
        Enum(ContainerType, name="container_type", create_type=False),
    )
    container_size: Mapped[ContainerSize | None] = mapped_column(
        Enum(ContainerSize, name="container_size", create_type=False),
    )

    amount_gram: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    amount_ml: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    reference_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("nutrition_references.id"),
    )
    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
