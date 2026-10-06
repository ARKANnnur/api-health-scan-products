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
from app.db.enums import ConsumptionType


class ScannedProduct(Base):
    __tablename__ = "scanned_products"

    __table_args__ = (
        CheckConstraint(
            "is_verified = false OR is_public = true",
            name="scanned_products_verified_implies_public_check",
        ),
        Index("idx_scanned_products_image_hash", "image_hash"),
        Index("idx_scanned_products_consumption_type", "consumption_type"),
        Index(
            "idx_scanned_products_barcode",
            "barcode",
            postgresql_where=text("barcode IS NOT NULL"),
        ),
        Index(
            "idx_scanned_products_content_hash",
            "content_hash",
            postgresql_where=text("content_hash IS NOT NULL"),
        ),
        Index(
            "idx_scanned_products_perceptual_hash",
            "perceptual_hash",
            postgresql_where=text("perceptual_hash IS NOT NULL"),
        ),
        Index("idx_scanned_products_created_by", "created_by"),
        Index(
            "idx_scanned_products_is_public",
            "is_public",
            postgresql_where=text("is_public = true"),
        ),
        Index(
            "idx_scanned_products_is_verified",
            "is_verified",
            postgresql_where=text("is_verified = true"),
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    product_name: Mapped[str] = mapped_column(Text)
    brand: Mapped[str | None] = mapped_column(String)
    consumption_type: Mapped[ConsumptionType] = mapped_column(
        Enum(ConsumptionType, name="consumption_type", create_type=False),
    )

    calories: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    caffeine_mg: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    saturated_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))

    serving_size_ml: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))
    serving_size_g: Mapped[Decimal | None] = mapped_column(Numeric(7, 2))

    image_hash: Mapped[str | None] = mapped_column(String, unique=True)
    barcode: Mapped[str | None] = mapped_column(String)
    content_hash: Mapped[str | None] = mapped_column(String)
    perceptual_hash: Mapped[str | None] = mapped_column(String)

    is_public: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
    )
    verified_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("profiles.id", ondelete="SET NULL"),
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_notes: Mapped[str | None] = mapped_column(Text)

    created_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("profiles.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )