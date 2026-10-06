from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class untuk semua SQLAlchemy models."""

    pass


# Import semua model di sini agar Alembic autogenerate bisa mendeteksi.
# WAJIB di paling bawah setelah Base didefinisikan.
from app.db import models  # noqa: E402, F401