import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_db import Base


class ScrapeRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapeTaskType(str, enum.Enum):
    SEARCH_PAGE = "search_page"
    JOB_DETAIL = "job_detail"


class ScrapeTaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PayloadType(str, enum.Enum):
    LISTING_JSON = "listing_json"
    DETAIL_JSON = "detail_json"
    LISTING_HTML = "listing_html"
    DETAIL_HTML = "detail_html"


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"
    __table_args__ = {"schema": "scraper"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    query: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ScrapeRunStatus] = mapped_column(
        Enum(ScrapeRunStatus, name="scrape_run_status_enum", schema="scraper"),
        default=ScrapeRunStatus.PENDING,
        nullable=False,
    )
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duplicates: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tasks: Mapped[list["ScrapeTask"]] = relationship(back_populates="scrape_run")


class ScrapeTask(Base):
    __tablename__ = "scrape_tasks"
    __table_args__ = (
        Index("ix_scrape_tasks_run_status", "scrape_run_id", "status"),
        Index("ix_scrape_tasks_board_status", "board", "status"),
        {"schema": "scraper"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scraper.scrape_runs.id"), nullable=False
    )
    task_type: Mapped[ScrapeTaskType] = mapped_column(
        Enum(ScrapeTaskType, name="scrape_task_type_enum", schema="scraper"), nullable=False
    )
    board: Mapped[str] = mapped_column(Text, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[ScrapeTaskStatus] = mapped_column(
        Enum(ScrapeTaskStatus, name="scrape_task_status_enum", schema="scraper"),
        default=ScrapeTaskStatus.PENDING,
        nullable=False,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scrape_run: Mapped[ScrapeRun] = relationship(back_populates="tasks")
    raw_payloads: Mapped[list["RawScrapePayload"]] = relationship(back_populates="scrape_task")


class RawScrapePayload(Base):
    __tablename__ = "raw_scrape_payloads"
    __table_args__ = {"schema": "scraper"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scraper.scrape_tasks.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    payload_type: Mapped[PayloadType] = mapped_column(
        Enum(PayloadType, name="payload_type_enum", schema="scraper"), nullable=False
    )
    raw_json: Mapped[dict | None] = mapped_column(JSONB)
    raw_html: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scrape_task: Mapped[ScrapeTask] = relationship(back_populates="raw_payloads")


class AdapterDiagnostic(Base):
    __tablename__ = "adapter_diagnostics"
    __table_args__ = {"schema": "scraper"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scrape_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scraper.scrape_tasks.id"), nullable=False, index=True
    )
    adapter_name: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

