from alembic import op

# ============================================================
# Trigger function: set_updated_at()
# ============================================================

def create_update_updated_at_function() -> None:
    """Bikin function `set_updated_at()` di Postgres.

    Cukup bikin SEKALI per database — dipakai oleh trigger
    `updated_at` di semua tabel yang punya kolom itu.
    """
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)


def drop_update_updated_at_function() -> None:
    """Drop function `set_updated_at()` (untuk downgrade)."""
    op.execute("DROP FUNCTION IF EXISTS set_updated_at() CASCADE")


def create_updated_at_trigger(table_name: str) -> None:
    """Bikin trigger updated_at untuk satu tabel.

    Contoh:
        create_updated_at_trigger("profiles")
        create_updated_at_trigger("scanned_products")
    """
    op.execute(f"""
        CREATE TRIGGER trg_{table_name}_updated_at
        BEFORE UPDATE ON {table_name}
        FOR EACH ROW
        EXECUTE FUNCTION set_updated_at();
    """)


def drop_updated_at_trigger(table_name: str) -> None:
    """Drop trigger updated_at (untuk downgrade)."""
    op.execute(
        f"DROP TRIGGER IF EXISTS trg_{table_name}_updated_at ON {table_name}"
    )
