from datetime import datetime

from pydantic import BaseModel


class NormalizedJobPayload(BaseModel):
    source_name: str
    source_type: str
    source_base_url: str
    external_job_id: str | None = None
    company_name: str
    company_website: str | None = None
    title: str
    location: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    work_mode: str = "unknown"
    employment_type: str = "unknown"
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str | None = None
    posted_at: datetime | None = None
    description: str
    short_description: str | None = None
    application_url: str | None = None
    job_url: str
    fingerprint: str
    first_seen_at: datetime
    last_seen_at: datetime
    raw_payload_url: str | None = None


class JobIngestRequest(BaseModel):
    jobs: list[NormalizedJobPayload]


class JobIngestResponse(BaseModel):
    inserted: int
    updated: int
    duplicates: int
    total_received: int

