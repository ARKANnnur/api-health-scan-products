"""nutri-103: schema

Revision ID: a6609a316935
Revises: d77bbeaa7559
Create Date: 2026-10-06 20:02:39.310245

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a6609a316935"
down_revision: str | Sequence[str] | None = "d77bbeaa7559"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ENUMS: dict[str, list[str]] = {
    "age_group": ["CHILD_SCHOOL", "TEEN", "YOUNG_ADULT", "MATURE_ELDER"],
    "consumption_type": ["SOLID", "LIQUID"],
    "measurement_type": ["SERVING", "VOLUME", "WEIGHT", "CONTAINER"],
    "container_type": [
        "GLASS",
        "CUP",
        "BOTTLE",
        "PLATE",
        "BOWL",
        "SPOON",
        "SCOOP",
        "PIECE",
        "SLICE",
        "HANDFUL",
        "PINCH",
        "CUSTOM",
    ],
    "container_size": ["SMALL", "MEDIUM", "LARGE"],
}


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def upgrade() -> None:
    # ========================================================================
    # 1. CREATE TYPES (enum)
    # ========================================================================
    for enum_name, values in ENUMS.items():
        vals = ", ".join(f"'{v}'" for v in values)
        op.execute(f"CREATE TYPE {enum_name} AS ENUM ({vals})")

    # ========================================================================
    # 2. TABLES
    # ========================================================================

    op.create_table(
        "nutrition_references",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("short_label", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("superseded_by", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["superseded_by"], ["nutrition_references.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_nutrition_references_category", "nutrition_references", ["category"])
    op.create_index(
        "idx_nutrition_references_effective",
        "nutrition_references",
        [sa.literal_column("effective_date DESC")],
    )

    op.create_table(
        "portion_references",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("measurement_type", _enum("measurement_type"), nullable=False),
        sa.Column("container_type", _enum("container_type"), nullable=True),
        sa.Column("container_size", _enum("container_size"), nullable=True),
        sa.Column("amount_gram", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("amount_ml", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("reference_id", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "(measurement_type = 'CONTAINER' AND container_type IS NOT NULL) OR measurement_type != 'CONTAINER'",
            name="portion_ref_container_check",
        ),
        sa.CheckConstraint(
            "(amount_gram IS NOT NULL AND amount_gram > 0) OR (amount_ml IS NOT NULL AND amount_ml > 0)",
            name="portion_ref_amount_check",
        ),
        sa.ForeignKeyConstraint(["reference_id"], ["nutrition_references.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_portion_references_category", "portion_references", ["category"])
    op.create_index(
        "idx_portion_references_container",
        "portion_references",
        ["container_type", "container_size"],
        postgresql_where=sa.text("container_type IS NOT NULL"),
    )
    op.create_index(
        "idx_portion_references_measurement", "portion_references", ["measurement_type"]
    )
    op.create_index("idx_portion_references_name", "portion_references", ["name"])
    op.create_index("idx_portion_references_reference_id", "portion_references", ["reference_id"])

    op.execute(
        """
        ALTER TABLE portion_references
        ADD CONSTRAINT unique_portion_ref
        UNIQUE NULLS NOT DISTINCT (name, measurement_type, container_type, container_size)
    """
    )

    op.create_table(
        "profiles",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("age_years", sa.Integer(), nullable=False),
        sa.Column("age_group", _enum("age_group"), nullable=False),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("height_cm", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "is_minor", sa.Boolean(), sa.Computed("age_years < 18", persisted=True), nullable=False
        ),
        sa.Column("disclaimer_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disclaimer_version", sa.String(), nullable=True),
        sa.Column("profile_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("gender IN ('MALE', 'FEMALE')", name="profiles_gender_check"),
        sa.CheckConstraint("age_years >= 7 AND age_years <= 120", name="profiles_age_years_check"),
        sa.CheckConstraint("height_cm >= 50 AND height_cm <= 250", name="profiles_height_cm_check"),
        sa.CheckConstraint("weight_kg >= 5 AND weight_kg <= 300", name="profiles_weight_kg_check"),
        sa.ForeignKeyConstraint(["id"], ["auth.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_profiles_id", "profiles", ["id"])
    op.create_index("idx_profiles_age_group", "profiles", ["age_group"])
    op.create_index(
        "idx_profiles_deleted_at",
        "profiles",
        ["deleted_at"],
        postgresql_where=sa.text("deleted_at IS NOT NULL"),
    )

    op.create_table(
        "consent_logs",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("user_email_snapshot", sa.String(), nullable=True),
        sa.Column("disclaimer_version", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "action IN ('accepted', 'rejected', 'revoked')", name="consent_logs_action_check"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_consent_logs_created_at", "consent_logs", [sa.literal_column("created_at DESC")]
    )
    op.create_index(
        "idx_consent_logs_email",
        "consent_logs",
        ["user_email_snapshot"],
        postgresql_where=sa.text("user_email_snapshot IS NOT NULL"),
    )
    op.create_index(
        "idx_consent_logs_user_created",
        "consent_logs",
        ["user_id", sa.literal_column("created_at DESC")],
    )
    op.create_index("idx_consent_logs_user_id", "consent_logs", ["user_id"])

    op.create_table(
        "daily_limits",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("bmr_kcal", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("tdee_kcal", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("calories_kcal", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("sugar_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("caffeine_mg", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("sodium_mg", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("saturated_fat_g", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("reference_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reference_ids", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column(
            "warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("computation_version", sa.String(), nullable=True),
        sa.Column("algorithm_hash", sa.String(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_daily_limits_computation_version", "daily_limits", ["computation_version"])
    op.create_index(
        "idx_daily_limits_computed_at", "daily_limits", [sa.literal_column("computed_at DESC")]
    )
    op.create_index(
        "idx_daily_limits_user_active_unique",
        "daily_limits",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_daily_limits_user_id", "daily_limits", ["user_id"])

    op.create_table(
        "scanned_products",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("product_name", sa.Text(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("consumption_type", _enum("consumption_type"), nullable=False),
        sa.Column("calories", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("caffeine_mg", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("saturated_fat_g", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("fiber_g", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("protein_g", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("serving_size_ml", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("serving_size_g", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("image_hash", sa.String(), nullable=True),
        sa.Column("barcode", sa.String(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("perceptual_hash", sa.String(), nullable=True),
        sa.Column("is_public", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("verified_by", sa.UUID(as_uuid=False), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "is_verified = false OR is_public = true",
            name="scanned_products_verified_implies_public_check",
        ),
        sa.ForeignKeyConstraint(["created_by"], ["profiles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["verified_by"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_hash"),
    )
    op.create_index(
        "idx_scanned_products_barcode",
        "scanned_products",
        ["barcode"],
        postgresql_where=sa.text("barcode IS NOT NULL"),
    )
    op.create_index(
        "idx_scanned_products_consumption_type", "scanned_products", ["consumption_type"]
    )
    op.create_index(
        "idx_scanned_products_content_hash",
        "scanned_products",
        ["content_hash"],
        postgresql_where=sa.text("content_hash IS NOT NULL"),
    )
    op.create_index("idx_scanned_products_created_by", "scanned_products", ["created_by"])
    op.create_index("idx_scanned_products_image_hash", "scanned_products", ["image_hash"])
    op.create_index(
        "idx_scanned_products_is_public",
        "scanned_products",
        ["is_public"],
        postgresql_where=sa.text("is_public = true"),
    )
    op.create_index(
        "idx_scanned_products_is_verified",
        "scanned_products",
        ["is_verified"],
        postgresql_where=sa.text("is_verified = true"),
    )
    op.create_index(
        "idx_scanned_products_perceptual_hash",
        "scanned_products",
        ["perceptual_hash"],
        postgresql_where=sa.text("perceptual_hash IS NOT NULL"),
    )

    op.execute(
        """
        CREATE INDEX idx_scanned_products_name_search
        ON scanned_products
        USING gin (to_tsvector('simple', product_name))
    """
    )

    op.create_table(
        "daily_intake_logs",
        sa.Column(
            "id",
            sa.UUID(as_uuid=False),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("product_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("consumption_type", _enum("consumption_type"), nullable=False),
        sa.Column("portion_consumed_amount", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("portion_servings", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("measurement_type", _enum("measurement_type"), nullable=True),
        sa.Column("container_type", _enum("container_type"), nullable=True),
        sa.Column("container_size", _enum("container_size"), nullable=True),
        sa.Column("input_method", sa.String(), nullable=True),
        sa.Column("estimated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("calories_kcal", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("sugar_g", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("sodium_mg", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("saturated_fat_g", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("caffeine_mg", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("client_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_id", sa.Text(), nullable=True),
        sa.Column("is_synced", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "logged_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.CheckConstraint(
            "input_method IS NULL OR input_method IN ('preset', 'custom', 'estimate', 'serving_size')",
            name="daily_intake_logs_input_method_check",
        ),
        sa.CheckConstraint(
            "portion_consumed_amount > 0 AND portion_consumed_amount <= 10000",
            name="daily_intake_logs_portion_amount_check",
        ),
        sa.CheckConstraint(
            "portion_servings IS NULL OR (portion_servings > 0 AND portion_servings <= 5)",
            name="daily_intake_logs_portion_servings_check",
        ),
        sa.ForeignKeyConstraint(["product_id"], ["scanned_products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_daily_intake_logs_device_id",
        "daily_intake_logs",
        ["device_id"],
        postgresql_where=sa.text("device_id IS NOT NULL"),
    )
    op.create_index(
        "idx_daily_intake_logs_is_synced",
        "daily_intake_logs",
        ["is_synced"],
        postgresql_where=sa.text("is_synced = false"),
    )
    op.create_index(
        "idx_daily_intake_logs_logged_at",
        "daily_intake_logs",
        [sa.literal_column("logged_at DESC")],
    )
    op.create_index("idx_daily_intake_logs_product_id", "daily_intake_logs", ["product_id"])
    op.create_index("idx_daily_intake_logs_user_id", "daily_intake_logs", ["user_id"])
    op.create_index(
        "idx_daily_intake_logs_user_logged",
        "daily_intake_logs",
        ["user_id", sa.literal_column("logged_at DESC")],
    )

    # ========================================================================
    # 3. TRIGGER FUNCTION + TRIGGERS
    # ========================================================================
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    for table in ("profiles", "nutrition_references", "scanned_products", "portion_references"):
        op.execute(
            f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION set_updated_at();
        """
        )

    # ========================================================================
    # 4. RLS ENABLE
    # ========================================================================
    for table in (
        "profiles",
        "daily_intake_logs",
        "consent_logs",
        "portion_references",
        "nutrition_references",
        "daily_limits",
        "scanned_products",
    ):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

    # ========================================================================
    # 5. POLICIES
    # ========================================================================
    op.execute(
        """
        CREATE POLICY "profiles_select_own" ON profiles FOR SELECT
        USING ((SELECT auth.uid()) = id)
    """
    )
    op.execute(
        """
        CREATE POLICY "profiles_insert_own" ON profiles FOR INSERT
        WITH CHECK ((SELECT auth.uid()) = id)
    """
    )
    op.execute(
        """
        CREATE POLICY "profiles_update_own" ON profiles FOR UPDATE
        USING ((SELECT auth.uid()) = id)
        WITH CHECK ((SELECT auth.uid()) = id)
    """
    )

    op.execute(
        """
        CREATE POLICY "logs_select_own" ON daily_intake_logs FOR SELECT
        USING ((SELECT auth.uid()) = user_id)
    """
    )
    op.execute(
        """
        CREATE POLICY "logs_insert_own" ON daily_intake_logs FOR INSERT
        WITH CHECK ((SELECT auth.uid()) = user_id)
    """
    )
    op.execute(
        """
        CREATE POLICY "logs_delete_own" ON daily_intake_logs FOR DELETE
        USING ((SELECT auth.uid()) = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "consent_select_own" ON consent_logs FOR SELECT
        USING ((SELECT auth.uid()) = user_id)
    """
    )
    op.execute(
        """
        CREATE POLICY "daily_limits_select_own" ON daily_limits FOR SELECT
        USING ((SELECT auth.uid()) = user_id)
    """
    )

    op.execute(
        """
        CREATE POLICY "portion_refs_select_authenticated" ON portion_references FOR SELECT
        USING (auth.role() = 'authenticated')
    """
    )
    op.execute(
        """
        CREATE POLICY "nutrition_refs_select_authenticated" ON nutrition_references FOR SELECT
        USING (auth.role() = 'authenticated')
    """
    )
    op.execute(
        """
        CREATE POLICY "scanned_products_select_own_or_public" ON scanned_products FOR SELECT
        USING ((SELECT auth.uid()) = created_by OR is_public = true)
    """
    )

    # ========================================================================
    # 6. GRANTS & REVOKES
    # ========================================================================
    op.execute("REVOKE ALL ON profiles FROM anon")
    op.execute("REVOKE ALL ON daily_intake_logs FROM anon")
    op.execute("REVOKE ALL ON consent_logs FROM anon")
    op.execute("REVOKE ALL ON daily_limits FROM anon")

    op.execute("REVOKE INSERT, UPDATE, DELETE ON consent_logs FROM authenticated")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON daily_limits FROM authenticated")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON nutrition_references FROM authenticated")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON portion_references FROM authenticated")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON scanned_products FROM authenticated")

    op.execute("GRANT SELECT ON scanned_products TO authenticated")
    op.execute("GRANT SELECT ON portion_references TO authenticated")
    op.execute("GRANT SELECT ON nutrition_references TO authenticated")
    op.execute("GRANT SELECT ON daily_limits TO authenticated")
    op.execute("GRANT SELECT, INSERT, DELETE ON daily_intake_logs TO authenticated")
    op.execute("GRANT SELECT, INSERT, UPDATE ON profiles TO authenticated")
    op.execute("GRANT SELECT ON consent_logs TO authenticated")

    op.execute("GRANT ALL ON scanned_products TO service_role")
    op.execute("GRANT ALL ON portion_references TO service_role")
    op.execute("GRANT ALL ON nutrition_references TO service_role")
    op.execute("GRANT ALL ON daily_limits TO service_role")
    op.execute("GRANT ALL ON consent_logs TO service_role")
    op.execute("GRANT ALL ON daily_intake_logs TO service_role")
    op.execute("GRANT ALL ON profiles TO service_role")


def downgrade() -> None:
    op.drop_table("daily_intake_logs")
    op.drop_table("scanned_products")
    op.drop_table("daily_limits")
    op.drop_table("consent_logs")
    op.drop_table("profiles")
    op.drop_table("portion_references")
    op.drop_table("nutrition_references")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at() CASCADE")

    for enum_name in reversed(list(ENUMS.keys())):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
