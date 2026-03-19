from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class JobSearchParams(BaseModel):
    q: str | None = None
    source: str | None = None
    company: str | None = None
    location: str | None = None
    work_mode: str | None = None
    employment_type: str | None = None
    posted_within_days: int | None = Field(default=None, ge=1, le=365)
    salary_min: Decimal | None = Field(default=None, ge=0)
    salary_max: Decimal | None = Field(default=None, ge=0)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort: str = "posted_at_desc"


class JobSummary(BaseModel):
    id: UUID
    title: str
    company: str
    source: str
    location: str | None = None
    work_mode: str
    employment_type: str
    posted_at: datetime | None = None
    salary_min: Decimal | None = None
    salary_max: Decimal | None = None
    currency: str | None = None
    is_active: bool


class JobDetail(JobSummary):
    description: str
    short_description: str | None = None
    application_url: str | None = None
    job_url: str
    first_seen_at: datetime
    last_seen_at: datetime


class PaginatedJobsResponse(BaseModel):
    items: list[JobSummary]
    page: int
    page_size: int
    total: int


class JobFilterMetadata(BaseModel):
    sources: list[str]
    companies: list[str]
    locations: list[str]
    work_modes: list[str]
    employment_types: list[str]

