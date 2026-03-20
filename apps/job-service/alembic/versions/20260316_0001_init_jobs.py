"""initial jobs schema

Revision ID: 20260316_0001
Revises:
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260316_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS jobs")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    work_mode_enum = postgresql.ENUM(
        "remote", "hybrid", "onsite", "unknown", name="work_mode_enum", schema="jobs", create_type=False
    )
    employment_type_enum = postgresql.ENUM(
        "full_time",
        "part_time",
        "contract",
        "internship",
        "temporary",
        "unknown",
        name="employment_type_enum",
        schema="jobs",
        create_type=False,
    )
    work_mode_enum.create(op.get_bind(), checkfirst=True)
    employment_type_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("normalized_name", name="uq_companies_normalized_name"),
        schema="jobs",
    )
    op.create_index(
        "ix_jobs_companies_normalized_name", "companies", ["normalized_name"], schema="jobs"
    )

    op.create_table(
        "job_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_name", name="uq_job_sources_source_name"),
        schema="jobs",
    )

    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_job_id", sa.String(length=255), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=128), nullable=True),
        sa.Column("state", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("work_mode", work_mode_enum, nullable=False),
        sa.Column("employment_type", employment_type_enum, nullable=False),
        sa.Column("salary_min", sa.Numeric(12, 2), nullable=True),
        sa.Column("salary_max", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("application_url", sa.Text(), nullable=True),
        sa.Column("job_url", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_jobs_salary_range",
        ),
        sa.ForeignKeyConstraint(["company_id"], ["jobs.companies.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["jobs.job_sources.id"]),
        sa.UniqueConstraint("fingerprint", name="uq_jobs_fingerprint"),
        sa.UniqueConstraint("source_id", "external_job_id", name="uq_jobs_source_external_job_id"),
        schema="jobs",
    )
    op.create_index("ix_jobs_jobs_source_id", "jobs", ["source_id"], schema="jobs")
    op.create_index("ix_jobs_jobs_company_id", "jobs", ["company_id"], schema="jobs")
    op.create_index("ix_jobs_jobs_posted_at", "jobs", ["posted_at"], schema="jobs")
    op.create_index("ix_jobs_jobs_is_active", "jobs", ["is_active"], schema="jobs")
    op.create_index(
        "ix_jobs_active_posted_id", "jobs", ["is_active", "posted_at", "id"], schema="jobs"
    )
    op.create_index(
        "ix_jobs_filters",
        "jobs",
        ["is_active", "work_mode", "employment_type", "posted_at"],
        schema="jobs",
    )


def downgrade() -> None:
    op.drop_index("ix_jobs_filters", table_name="jobs", schema="jobs")
    op.drop_index("ix_jobs_active_posted_id", table_name="jobs", schema="jobs")
    op.drop_index("ix_jobs_jobs_is_active", table_name="jobs", schema="jobs")
    op.drop_index("ix_jobs_jobs_posted_at", table_name="jobs", schema="jobs")
    op.drop_index("ix_jobs_jobs_company_id", table_name="jobs", schema="jobs")
    op.drop_index("ix_jobs_jobs_source_id", table_name="jobs", schema="jobs")
    op.drop_table("jobs", schema="jobs")
    op.drop_table("job_sources", schema="jobs")
    op.drop_index("ix_jobs_companies_normalized_name", table_name="companies", schema="jobs")
    op.drop_table("companies", schema="jobs")
    postgresql.ENUM(name="employment_type_enum", schema="jobs").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="work_mode_enum", schema="jobs").drop(op.get_bind(), checkfirst=True)
