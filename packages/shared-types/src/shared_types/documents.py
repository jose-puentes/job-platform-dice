from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateDocumentRequest(BaseModel):
    job_id: UUID
    document_type: str
    requested_by: str = "user"


class EnsureDocumentsRequest(BaseModel):
    job_id: UUID
    document_types: list[str]
    requested_by: str = "system"


class GenerationRunResponse(BaseModel):
    id: UUID
    job_id: UUID
    document_type: str
    status: str
    model_name: str
    requested_by: str | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentResponse(BaseModel):
    id: UUID
    job_id: UUID
    document_type: str
    generation_status: str
    file_path: str
    model_name: str
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]


class EnsureDocumentsResponse(BaseModel):
    documents: list[DocumentResponse]
    queued_runs: list[GenerationRunResponse]

