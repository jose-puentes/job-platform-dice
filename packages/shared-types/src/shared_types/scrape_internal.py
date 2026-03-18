from uuid import UUID

from pydantic import BaseModel


class ScrapeTaskStatusUpdateRequest(BaseModel):
    scrape_task_id: UUID
    status: str
    attempt_count: int | None = None
    error_message: str | None = None
    total_found: int | None = None
    total_inserted: int | None = None
    total_updated: int | None = None
    total_duplicates: int | None = None

