from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConsentLog(Base):
    __tablename__ = "consent_logs"

    __table_args__ = (
        CheckConstraint(
            "action IN ('accepted', 'rejected', 'revoked')",
            name="consent_logs_action_check",
        ),
        Index("idx_consent_logs_user_id", "user_id"),
        Index(
            "idx_consent_logs_user_created",
            "user_id",
            text("created_at DESC"),
        ),
        Index(
            "idx_consent_logs_created_at",
            text("created_at DESC"),
        ),
        Index(
            "idx_consent_logs_email",
            "user_email_snapshot",
            postgresql_where=text("user_email_snapshot IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("profiles.id", ondelete="SET NULL"),
    )
    user_email_snapshot: Mapped[str | None] = mapped_column(String)
    disclaimer_version: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    ip_address: Mapped[str | None] = mapped_column(INET)
    user_agent: Mapped[str | None] = mapped_column(Text)
