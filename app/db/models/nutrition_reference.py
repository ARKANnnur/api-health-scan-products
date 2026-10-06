from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NutritionReference(Base):
    __tablename__ = "nutrition_references"

    # ---- Primary key ----
    # Text PK (bukan UUID) karena ini data referensi yang punya ID manusiawi:
    # contoh: "kemenkes_akg_2019", "who_sugar_2015"
    id: Mapped[str] = mapped_column(String, primary_key=True)

    # ---- Display fields ----
    label: Mapped[str] = mapped_column(String)
    short_label: Mapped[str | None] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String)

    # ---- Kategorisasi ----
    # Contoh nilai: "government", "international", "research"
    category: Mapped[str | None] = mapped_column(String)
    year: Mapped[int | None] = mapped_column(Integer)

    # ---- Versioning ----
    version: Mapped[str | None] = mapped_column(String)          # "2019", "2024"
    effective_date: Mapped[date | None] = mapped_column(Date)     # kapan mulai berlaku

    # Self-referential FK: versi lama -> versi baru
    # Kalau guideline baru terbit, row lama di-update: superseded_by = "id_baru"
    # Yang baru TETAP ada (ga dihapus), yang lama ditandai
    superseded_by: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("nutrition_references.id"),
    )

    # ---- Timestamps ----
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )