import sys
from pathlib import Path

# Tambah root project ke sys.path biar bisa import `app.*`
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from typing import Any  # noqa: E402

from sqlalchemy import inspect  # noqa: E402

# WAJIB import Base biar semua model ke-load
from app.db.base import Base  # noqa: E402


def list_tables() -> None:
    """List semua tabel yang ke-detect oleh Base.metadata."""
    tables = sorted(Base.metadata.tables.keys())
    print("=" * 70)
    print(f"TABLES REGISTERED ({len(tables)})")
    print("=" * 70)
    for t in tables:
        print(f"  - {t}")
    print()


def inspect_table(model_name: str) -> None:
    """Print semua kolom + constraint dari model."""
    # Cari model di registry
    model_class: Any = None
    for mapper in Base.registry.mappers:
        if mapper.class_.__name__ == model_name:
            model_class = mapper.class_
            break

    if model_class is None:
        print(f"[X] Model '{model_name}' tidak ditemukan.")
        print(f"    Model yang terdaftar: {[m.class_.__name__ for m in Base.registry.mappers]}")
        return

    mapper = inspect(model_class)
    print("=" * 70)
    print(f"MODEL: {model_name}")
    print(f"TABLE: {mapper.local_table.name}")
    print("=" * 70)

    # Columns
    print(f"\n{'COLUMN':<25} {'TYPE':<30} {'NULL':<6} {'PK':<4}")
    print("-" * 70)
    for col in mapper.columns:
        col_type = str(col.type)[:28]
        nullable = "YES" if col.nullable else "NO"
        pk = "YES" if col.primary_key else ""
        print(f"{col.name:<25} {col_type:<30} {nullable:<6} {pk:<4}")

    # Foreign Keys
    fks = list(mapper.local_table.foreign_keys)
    if fks:
        print(f"\nFOREIGN KEYS ({len(fks)}):")
        for fk in fks:
            print(f"  {fk.parent.name} -> {fk.target_fullname}")

    # Constraints
    constraints = mapper.local_table.constraints
    checks = [c for c in constraints if hasattr(c, "sqltext")]
    uniques = [c for c in constraints if c.__class__.__name__ == "UniqueConstraint"]

    if checks:
        print(f"\nCHECK CONSTRAINTS ({len(checks)}):")
        for c in checks:
            print(f"  {c.name}: {c.sqltext}")

    if uniques:
        print(f"\nUNIQUE CONSTRAINTS ({len(uniques)}):")
        for c in uniques:
            cols = ", ".join(col.name for col in c.columns)
            print(f"  {c.name or '(unnamed)'}: ({cols})")

    # Indexes
    indexes = list(mapper.local_table.indexes)
    if indexes:
        print(f"\nINDEXES ({len(indexes)}):")
        for idx in indexes:
            cols = ", ".join(col.name for col in idx.columns)
            unique = " [UNIQUE]" if idx.unique else ""
            print(f"  {idx.name}: ({cols}){unique}")

    print()


def main() -> None:
    # Selalu list tables dulu
    list_tables()

    # Kalau ada argumen, inspect model spesifik
    if len(sys.argv) > 1:
        for model_name in sys.argv[1:]:
            inspect_table(model_name)
    else:
        # Tanpa argumen, inspect semua model
        for mapper in Base.registry.mappers:
            inspect_table(mapper.class_.__name__)


if __name__ == "__main__":
    main()
