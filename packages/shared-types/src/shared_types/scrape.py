from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CreateScrapeRunRequest(BaseModel):
    source: str
    query: str | None = None
    location: str | None = None
    max_pages: int = Field(default=1, ge=1, le=25)


class ScrapeRunResponse(BaseModel):
    id: UUID
    source: str
    query: str | None = None
    location: str | None = None
    status: str
    total_tasks: int
    completed_tasks: int
    total_found: int
    total_inserted: int
    total_updated: int
    total_duplicates: int
    total_failed: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ScrapeRunListResponse(BaseModel):
    items: list[ScrapeRunResponse]


class ScrapeTaskPayload(BaseModel):
    scrape_run_id: UUID
    scrape_task_id: UUID
    source: str
    query: str | None = None
    location: str | None = None
    page_number: int

