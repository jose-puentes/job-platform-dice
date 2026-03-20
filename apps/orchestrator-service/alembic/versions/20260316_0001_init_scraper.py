"""initial scraper schema

Revision ID: 20260316_scraper_0001
Revises:
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260316_scraper_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS scraper")

    run_status_enum = postgresql.ENUM(
        "pending", "running", "partial", "completed", "failed",
        name="scrape_run_status_enum", schema="scraper", create_type=False
    )
    task_type_enum = postgresql.ENUM(
        "search_page", "job_detail", name="scrape_task_type_enum", schema="scraper", create_type=False
    )
    task_status_enum = postgresql.ENUM(
        "pending", "running", "completed", "failed",
        name="scrape_task_status_enum", schema="scraper", create_type=False
    )
    payload_type_enum = postgresql.ENUM(
        "listing_json", "detail_json", "listing_html", "detail_html",
        name="payload_type_enum", schema="scraper", create_type=False
    )
    for enum_type in (run_status_enum, task_type_enum, task_status_enum, payload_type_enum):
        enum_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scrape_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("query", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("status", run_status_enum, nullable=False),
        sa.Column("total_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_tasks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_inserted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_updated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="scraper",
    )

    op.create_table(
        "scrape_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scrape_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", task_type_enum, nullable=False),
        sa.Column("board", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("status", task_status_enum, nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_run_id"], ["scraper.scrape_runs.id"]),
        schema="scraper",
    )
    op.create_index("ix_scrape_tasks_run_status", "scrape_tasks", ["scrape_run_id", "status"], schema="scraper")
    op.create_index("ix_scrape_tasks_board_status", "scrape_tasks", ["board", "status"], schema="scraper")

    op.create_table(
        "raw_scrape_payloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scrape_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("payload_type", payload_type_enum, nullable=False),
        sa.Column("raw_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_task_id"], ["scraper.scrape_tasks.id"]),
        schema="scraper",
    )
    op.create_index("ix_scraper_raw_scrape_task_id", "raw_scrape_payloads", ["scrape_task_id"], schema="scraper")

    op.create_table(
        "adapter_diagnostics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("scrape_task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("adapter_name", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["scrape_task_id"], ["scraper.scrape_tasks.id"]),
        schema="scraper",
    )


def downgrade() -> None:
    op.drop_table("adapter_diagnostics", schema="scraper")
    op.drop_index("ix_scraper_raw_scrape_task_id", table_name="raw_scrape_payloads", schema="scraper")
    op.drop_table("raw_scrape_payloads", schema="scraper")
    op.drop_index("ix_scrape_tasks_board_status", table_name="scrape_tasks", schema="scraper")
    op.drop_index("ix_scrape_tasks_run_status", table_name="scrape_tasks", schema="scraper")
    op.drop_table("scrape_tasks", schema="scraper")
    op.drop_table("scrape_runs", schema="scraper")
    for enum_name in (
        "payload_type_enum",
        "scrape_task_status_enum",
        "scrape_task_type_enum",
        "scrape_run_status_enum",
    ):
        postgresql.ENUM(name=enum_name, schema="scraper").drop(op.get_bind(), checkfirst=True)
