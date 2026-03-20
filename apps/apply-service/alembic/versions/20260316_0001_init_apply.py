"""initial apply schema

Revision ID: 20260316_apply_0001
Revises:
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260316_apply_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS apply")

    apply_mode_enum = postgresql.ENUM("single", "batch", name="apply_mode_enum", schema="apply", create_type=False)
    apply_run_status_enum = postgresql.ENUM(
        "pending", "running", "partial", "completed", "failed",
        name="apply_run_status_enum", schema="apply", create_type=False
    )
    application_status_enum = postgresql.ENUM(
        "pending", "processing", "applied", "manual_assist", "failed",
        name="application_status_enum", schema="apply", create_type=False
    )
    apply_strategy_enum = postgresql.ENUM(
        "easy_apply", "external_redirect", "manual_assist",
        name="apply_strategy_enum", schema="apply", create_type=False
    )
    apply_attempt_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="apply_attempt_status_enum", schema="apply", create_type=False
    )
    for enum_type in (
        apply_mode_enum,
        apply_run_status_enum,
        application_status_enum,
        apply_strategy_enum,
        apply_attempt_status_enum,
    ):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "apply_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("triggered_by", sa.Text(), nullable=False),
        sa.Column("mode", apply_mode_enum, nullable=False),
        sa.Column("status", apply_run_status_enum, nullable=False),
        sa.Column("total_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_jobs", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="apply",
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_status", application_status_enum, nullable=False),
        sa.Column("apply_strategy", apply_strategy_enum, nullable=False),
        sa.Column("resume_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("cover_letter_document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="apply",
    )
    op.create_index("ix_applications_job_created", "applications", ["job_id", "created_at"], schema="apply")
    op.create_index("ix_apply_applications_job_id", "applications", ["job_id"], schema="apply")

    op.create_table(
        "application_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["apply.applications.id"]),
        schema="apply",
    )
    op.create_index(
        "ix_application_events_application_created",
        "application_events",
        ["application_id", "created_at"],
        schema="apply",
    )

    op.create_table(
        "apply_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("apply_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("strategy", apply_strategy_enum, nullable=False),
        sa.Column("status", apply_attempt_status_enum, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["apply_run_id"], ["apply.apply_runs.id"]),
        sa.UniqueConstraint("apply_run_id", "job_id", name="uq_apply_attempts_run_job"),
        schema="apply",
    )
    op.create_index("ix_apply_attempts_job_id", "apply_attempts", ["job_id"], schema="apply")


def downgrade() -> None:
    op.drop_index("ix_apply_attempts_job_id", table_name="apply_attempts", schema="apply")
    op.drop_table("apply_attempts", schema="apply")
    op.drop_index("ix_application_events_application_created", table_name="application_events", schema="apply")
    op.drop_table("application_events", schema="apply")
    op.drop_index("ix_apply_applications_job_id", table_name="applications", schema="apply")
    op.drop_index("ix_applications_job_created", table_name="applications", schema="apply")
    op.drop_table("applications", schema="apply")
    op.drop_table("apply_runs", schema="apply")
    for enum_name in (
        "apply_attempt_status_enum",
        "apply_strategy_enum",
        "application_status_enum",
        "apply_run_status_enum",
        "apply_mode_enum",
    ):
        postgresql.ENUM(name=enum_name, schema="apply").drop(op.get_bind(), checkfirst=True)
