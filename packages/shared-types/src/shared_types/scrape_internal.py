from uuid import UUID

from pydantic import BaseModel, Field


class ScrapeTaskStatusUpdateRequest(BaseModel):
    scrape_task_id: UUID
    status: str
    attempt_count: int | None = None
    error_message: str | None = None
    total_found: int | None = None
    total_inserted: int | None = None
    total_updated: int | None = None
    total_duplicates: int | None = None


class RawScrapePayloadArtifact(BaseModel):
    source: str
    source_url: str
    payload_type: str
    raw_json: dict | None = None
    raw_html: str | None = None


class AdapterDiagnosticArtifact(BaseModel):
    adapter_name: str
    severity: str
    message: str
    metadata: dict = Field(default_factory=dict)


class ScrapeTaskArtifactsRequest(BaseModel):
    scrape_task_id: UUID
    raw_payloads: list[RawScrapePayloadArtifact] = Field(default_factory=list)
    diagnostics: list[AdapterDiagnosticArtifact] = Field(default_factory=list)

