from sqlalchemy import Column, Table
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base

auth_users = Table(
    "users",
    Base.metadata,
    Column("id", UUID(as_uuid=False), primary_key=True),
    schema="auth",
    info={"skip_autogenerate": True},
)
