"""initial ai schema

Revision ID: 20260316_ai_0001
Revises:
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260316_ai_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS ai")

    template_type_enum = postgresql.ENUM(
        "resume", "cover_letter", name="template_type_enum", schema="ai"
    )
    document_type_enum = postgresql.ENUM(
        "resume", "cover_letter", name="document_type_enum", schema="ai"
    )
    generation_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed", name="generation_status_enum", schema="ai"
    )
    for enum_type in (template_type_enum, document_type_enum, generation_status_enum):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("template_type", template_type_enum, nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("template_type", "name", "version", name="uq_prompt_templates_type_name_version"),
        schema="ai",
    )

    op.create_table(
        "generation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", document_type_enum, nullable=False),
        sa.Column("status", generation_status_enum, nullable=False),
        sa.Column("prompt_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="ai",
    )
    op.create_index("ix_ai_generation_runs_job_id", "generation_runs", ["job_id"], schema="ai")

    op.create_table(
        "generated_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_type", document_type_enum, nullable=False),
        sa.Column("prompt_template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("generation_status", generation_status_enum, nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="ai",
    )
    op.create_index("ix_ai_generated_documents_job_id", "generated_documents", ["job_id"], schema="ai")
    op.create_index(
        "ix_generated_documents_job_type_created",
        "generated_documents",
        ["job_id", "document_type", "created_at"],
        schema="ai",
    )


def downgrade() -> None:
    op.drop_index("ix_generated_documents_job_type_created", table_name="generated_documents", schema="ai")
    op.drop_index("ix_ai_generated_documents_job_id", table_name="generated_documents", schema="ai")
    op.drop_table("generated_documents", schema="ai")
    op.drop_index("ix_ai_generation_runs_job_id", table_name="generation_runs", schema="ai")
    op.drop_table("generation_runs", schema="ai")
    op.drop_table("prompt_templates", schema="ai")
    for enum_name in ("generation_status_enum", "document_type_enum", "template_type_enum"):
        postgresql.ENUM(name=enum_name, schema="ai").drop(op.get_bind(), checkfirst=True)
