import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_db import Base


class ApplyMode(str, enum.Enum):
    SINGLE = "single"
    BATCH = "batch"


class ApplyRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    APPLIED = "applied"
    MANUAL_ASSIST = "manual_assist"
    FAILED = "failed"


class ApplyStrategy(str, enum.Enum):
    EASY_APPLY = "easy_apply"
    EXTERNAL_REDIRECT = "external_redirect"
    MANUAL_ASSIST = "manual_assist"


class ApplyAttemptStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ApplyRun(Base):
    __tablename__ = "apply_runs"
    __table_args__ = {"schema": "apply"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triggered_by: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[ApplyMode] = mapped_column(
        ENUM(ApplyMode, name="apply_mode_enum", schema="apply", create_type=False),
        nullable=False,
    )
    status: Mapped[ApplyRunStatus] = mapped_column(
        ENUM(ApplyRunStatus, name="apply_run_status_enum", schema="apply", create_type=False),
        default=ApplyRunStatus.PENDING,
        nullable=False,
    )
    total_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_jobs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    attempts: Mapped[list["ApplyAttempt"]] = relationship(back_populates="apply_run")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_job_created", "job_id", "created_at"), {"schema": "apply"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    application_status: Mapped[ApplicationStatus] = mapped_column(
        ENUM(ApplicationStatus, name="application_status_enum", schema="apply", create_type=False),
        nullable=False,
    )
    apply_strategy: Mapped[ApplyStrategy] = mapped_column(
        ENUM(ApplyStrategy, name="apply_strategy_enum", schema="apply", create_type=False),
        nullable=False,
    )
    resume_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    cover_letter_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    external_reference: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    events: Mapped[list["ApplicationEvent"]] = relationship(back_populates="application")


class ApplicationEvent(Base):
    __tablename__ = "application_events"
    __table_args__ = (Index("ix_application_events_application_created", "application_id", "created_at"), {"schema": "apply"})

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("apply.applications.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="events")


class ApplyAttempt(Base):
    __tablename__ = "apply_attempts"
    __table_args__ = (
        UniqueConstraint("apply_run_id", "job_id", name="uq_apply_attempts_run_job"),
        {"schema": "apply"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    apply_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("apply.apply_runs.id"), nullable=False
    )
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    strategy: Mapped[ApplyStrategy] = mapped_column(
        ENUM(ApplyStrategy, name="apply_strategy_enum", schema="apply", create_type=False),
        nullable=False,
    )
    status: Mapped[ApplyAttemptStatus] = mapped_column(
        ENUM(ApplyAttemptStatus, name="apply_attempt_status_enum", schema="apply", create_type=False),
        default=ApplyAttemptStatus.PENDING,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    apply_run: Mapped[ApplyRun] = relationship(back_populates="attempts")

