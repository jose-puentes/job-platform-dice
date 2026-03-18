from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateSingleApplyRequest(BaseModel):
    job_id: UUID
    triggered_by: str = "user"


class CreateBatchApplyRequest(BaseModel):
    job_ids: list[UUID]
    triggered_by: str = "user"


class ApplyRunResponse(BaseModel):
    id: UUID
    triggered_by: str
    mode: str
    status: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationResponse(BaseModel):
    id: UUID
    job_id: UUID
    application_status: str
    apply_strategy: str
    resume_document_id: UUID | None = None
    cover_letter_document_id: UUID | None = None
    applied_at: datetime | None = None
    external_reference: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]


class ApplyAttemptPayload(BaseModel):
    apply_run_id: UUID
    job_id: UUID
    triggered_by: str = "system"

