import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared_db import Base


class WorkMode(str, enum.Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    UNKNOWN = "unknown"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = {"schema": "jobs"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    website: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="company")


class JobSource(Base):
    __tablename__ = "job_sources"
    __table_args__ = {"schema": "jobs"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source_type: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    jobs: Mapped[list["Job"]] = relationship(back_populates="source")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("source_id", "external_job_id", name="uq_jobs_source_external_job_id"),
        UniqueConstraint("fingerprint", name="uq_jobs_fingerprint"),
        CheckConstraint("salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max", name="ck_jobs_salary_range"),
        Index("ix_jobs_active_posted_id", "is_active", "posted_at", "id"),
        Index("ix_jobs_filters", "is_active", "work_mode", "employment_type", "posted_at"),
        {"schema": "jobs"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_sources.id"), nullable=False, index=True
    )
    external_job_id: Mapped[str | None] = mapped_column(String(255))
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.companies.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(128))
    state: Mapped[str | None] = mapped_column(String(128))
    city: Mapped[str | None] = mapped_column(String(128))
    work_mode: Mapped[WorkMode] = mapped_column(
        ENUM(
            WorkMode,
            name="work_mode_enum",
            schema="jobs",
            create_type=False,
            values_callable=enum_values,
        ),
        default=WorkMode.UNKNOWN,
        nullable=False,
    )
    employment_type: Mapped[EmploymentType] = mapped_column(
        ENUM(
            EmploymentType,
            name="employment_type_enum",
            schema="jobs",
            create_type=False,
            values_callable=enum_values,
        ),
        default=EmploymentType.UNKNOWN,
        nullable=False,
    )
    salary_min: Mapped[float | None] = mapped_column(Numeric(12, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text)
    application_url: Mapped[str | None] = mapped_column(Text)
    job_url: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    company: Mapped[Company] = relationship(back_populates="jobs")
    source: Mapped[JobSource] = relationship(back_populates="jobs")

