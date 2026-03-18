from uuid import UUID

from fastapi import APIRouter

from app.clients.services import ai_service_client
from shared_types import (
    CreateDocumentRequest,
    DocumentListResponse,
    DocumentResponse,
    GenerationRunResponse,
)

router = APIRouter(tags=["documents"])


@router.post("/api/v1/jobs/{job_id}/documents/resume", response_model=GenerationRunResponse)
async def generate_resume(job_id: UUID) -> GenerationRunResponse:
    async with ai_service_client() as client:
        response = await client.post(
            "/internal/generations",
            json=CreateDocumentRequest(job_id=job_id, document_type="resume").model_dump(mode="json"),
        )
        response.raise_for_status()
        return GenerationRunResponse.model_validate(response.json())


@router.post("/api/v1/jobs/{job_id}/documents/cover-letter", response_model=GenerationRunResponse)
async def generate_cover_letter(job_id: UUID) -> GenerationRunResponse:
    async with ai_service_client() as client:
        response = await client.post(
            "/internal/generations",
            json=CreateDocumentRequest(job_id=job_id, document_type="cover_letter").model_dump(mode="json"),
        )
        response.raise_for_status()
        return GenerationRunResponse.model_validate(response.json())


@router.get("/api/v1/jobs/{job_id}/documents", response_model=DocumentListResponse)
async def list_documents(job_id: UUID) -> DocumentListResponse:
    async with ai_service_client() as client:
        response = await client.get(f"/internal/jobs/{job_id}/documents")
        response.raise_for_status()
        return DocumentListResponse.model_validate(response.json())


@router.get("/api/v1/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID) -> DocumentResponse:
    async with ai_service_client() as client:
        response = await client.get(f"/internal/documents/{document_id}")
        response.raise_for_status()
        return DocumentResponse.model_validate(response.json())

