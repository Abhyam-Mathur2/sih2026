"""Initial schema – all tables for BMIM with pgvector support

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Supabase notes:
  - pgvector is pre-installed on all Supabase projects; no manual setup needed.
  - uuid-ossp is also available by default.
  - The VECTOR_BACKEND env var controls whether pgvector or a TEXT fallback
    is used at the Python model level. This migration always creates the real
    vector column when VECTOR_BACKEND=pgvector (the default for Supabase).
  - Run with:  alembic upgrade head
"""

import os
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

# Respect VECTOR_BACKEND from environment; Supabase users should leave this
# as "pgvector" (the default). Set to "local" only for offline development
# without a Supabase connection.
_VECTOR_BACKEND = os.environ.get("VECTOR_BACKEND", "pgvector").lower()


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Extensions
    # ------------------------------------------------------------------
    # IF NOT EXISTS is safe for a fresh Supabase project and keeps the schema
    # aligned with the pgvector ORM model. Do not swallow an extension error:
    # PostgreSQL marks the transaction failed after such an error, and a text
    # fallback would leave an incompatible production schema.
    if _VECTOR_BACKEND == "pgvector":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    except Exception:
        pass  # Non-critical

    # ------------------------------------------------------------------
    # cpses
    # ------------------------------------------------------------------
    op.create_table(
        "cpses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("short_code", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("short_code"),
    )
    op.create_index("ix_cpses_id", "cpses", ["id"])
    op.create_index("ix_cpses_short_code", "cpses", ["short_code"])

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "CPSE_MANAGER", "TECHNICAL_REVIEWER", name="userrole"), nullable=False),
        sa.Column("cpse_id", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["cpse_id"], ["cpses.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_cpse_id", "users", ["cpse_id"])

    # ------------------------------------------------------------------
    # material_categories
    # ------------------------------------------------------------------
    op.create_table(
        "material_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["material_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_material_categories_id", "material_categories", ["id"])

    # ------------------------------------------------------------------
    # upload_jobs
    # ------------------------------------------------------------------
    op.create_table(
        "upload_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cpse_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=True),  # Supabase Storage path
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", "PARTIAL", name="uploadstatus"), nullable=False),
        sa.Column("error_summary", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["cpse_id"], ["cpses.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_jobs_id", "upload_jobs", ["id"])
    op.create_index("ix_upload_jobs_cpse_id", "upload_jobs", ["cpse_id"])
    op.create_index("ix_upload_jobs_status", "upload_jobs", ["status"])

    # ------------------------------------------------------------------
    # materials
    # ------------------------------------------------------------------
    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cpse_id", sa.Integer(), nullable=False),
        sa.Column("legacy_material_code", sa.String(100), nullable=False),
        sa.Column("original_description", sa.Text(), nullable=False),
        sa.Column("normalized_description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("unit_of_measure", sa.String(50), nullable=True),
        sa.Column("manufacturer", sa.String(200), nullable=True),
        sa.Column("status", sa.Enum("ACTIVE", "PENDING_REVIEW", "MAPPED", "REJECTED", name="materialstatus"), nullable=False, server_default="ACTIVE"),
        sa.Column("upload_job_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["cpse_id"], ["cpses.id"]),
        sa.ForeignKeyConstraint(["category_id"], ["material_categories.id"]),
        sa.ForeignKeyConstraint(["upload_job_id"], ["upload_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_materials_id", "materials", ["id"])
    op.create_index("ix_materials_cpse_id", "materials", ["cpse_id"])
    op.create_index("ix_materials_legacy_material_code", "materials", ["legacy_material_code"])
    op.create_index("ix_materials_category_id", "materials", ["category_id"])
    op.create_index("ix_materials_status", "materials", ["status"])

    # ------------------------------------------------------------------
    # material_attributes
    # ------------------------------------------------------------------
    op.create_table(
        "material_attributes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("attribute_name", sa.String(100), nullable=False),
        sa.Column("attribute_value", sa.String(500), nullable=False),
        sa.Column("normalized_value", sa.String(500), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_material_attributes_id", "material_attributes", ["id"])
    op.create_index("ix_material_attributes_material_id", "material_attributes", ["material_id"])

    # ------------------------------------------------------------------
    # material_embeddings (pgvector OR text fallback)
    # ------------------------------------------------------------------
    if _VECTOR_BACKEND == "pgvector":
        from pgvector.sqlalchemy import Vector  # type: ignore
        op.create_table(
            "material_embeddings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.Integer(), nullable=False),
            sa.Column("model_name", sa.String(100), nullable=False),
            sa.Column("embedding", Vector(384), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("material_id"),
        )
        # IVFFlat index for approximate nearest-neighbour search.
        # Note: requires at least one row before it can be built.
        # On an empty DB this is created proactively; it becomes useful once data is loaded.
        try:
            op.execute(
                "CREATE INDEX ix_material_embeddings_ivfflat "
                "ON material_embeddings "
                "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10)"
            )
        except Exception:
            pass  # Will be created lazily once data exists
    else:
        # TEXT fallback – JSON array stored as text
        op.create_table(
            "material_embeddings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("material_id", sa.Integer(), nullable=False),
            sa.Column("model_name", sa.String(100), nullable=False),
            sa.Column("embedding", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("material_id"),
        )

    op.create_index("ix_material_embeddings_id", "material_embeddings", ["id"])
    op.create_index("ix_material_embeddings_material_id", "material_embeddings", ["material_id"])

    # ------------------------------------------------------------------
    # national_materials
    # ------------------------------------------------------------------
    op.create_table(
        "national_materials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("national_material_code", sa.String(100), nullable=False),
        sa.Column("standard_description", sa.Text(), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("standard_attributes", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "ACTIVE", "DEPRECATED", name="nationalmaterialstatus"), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["material_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("national_material_code"),
    )
    op.create_index("ix_national_materials_id", "national_materials", ["id"])
    op.create_index("ix_national_materials_code", "national_materials", ["national_material_code"])
    op.create_index("ix_national_materials_status", "national_materials", ["status"])

    # ------------------------------------------------------------------
    # material_matches
    # ------------------------------------------------------------------
    op.create_table(
        "material_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_material_id", sa.Integer(), nullable=False),
        sa.Column("candidate_material_id", sa.Integer(), nullable=False),
        sa.Column("semantic_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("fuzzy_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("attribute_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("technical_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("final_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("match_type", sa.Enum("IDENTICAL", "NEAR_DUPLICATE", "FUNCTIONALLY_EQUIVALENT", "DIFFERENT", name="matchtype"), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "APPROVED", "REJECTED", "MODIFIED", name="matchstatus"), nullable=False, server_default="PENDING"),
        sa.Column("explanation", postgresql.JSONB(), nullable=True),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewer_comment", sa.String(1000), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_material_id"], ["materials.id"]),
        sa.ForeignKeyConstraint(["candidate_material_id"], ["materials.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_material_matches_id", "material_matches", ["id"])
    op.create_index("ix_material_matches_source", "material_matches", ["source_material_id"])
    op.create_index("ix_material_matches_candidate", "material_matches", ["candidate_material_id"])
    op.create_index("ix_material_matches_status", "material_matches", ["status"])
    op.create_index("ix_material_matches_score", "material_matches", ["final_score"])

    # ------------------------------------------------------------------
    # material_mappings
    # ------------------------------------------------------------------
    op.create_table(
        "material_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("national_material_id", sa.Integer(), nullable=False),
        sa.Column("mapping_status", sa.Enum("PENDING", "APPROVED", "REJECTED", name="mappingstatus"), nullable=False, server_default="PENDING"),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.ForeignKeyConstraint(["national_material_id"], ["national_materials.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_material_mappings_id", "material_mappings", ["id"])
    op.create_index("ix_material_mappings_material_id", "material_mappings", ["material_id"])
    op.create_index("ix_material_mappings_national_id", "material_mappings", ["national_material_id"])

    # ------------------------------------------------------------------
    # audit_logs
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("old_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_id", "audit_logs", ["id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("material_mappings")
    op.drop_table("material_matches")
    op.drop_table("material_embeddings")
    op.drop_table("material_attributes")
    op.drop_table("materials")
    op.drop_table("upload_jobs")
    op.drop_table("national_materials")
    op.drop_table("material_categories")
    op.drop_table("users")
    op.drop_table("cpses")

    for enum_name in [
        "userrole", "materialstatus", "matchtype", "matchstatus",
        "nationalmaterialstatus", "mappingstatus", "uploadstatus",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
