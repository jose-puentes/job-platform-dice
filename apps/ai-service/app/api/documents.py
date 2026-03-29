from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.document_service import DocumentService
from shared_types import (
    CreateDocumentRequest,
    DocumentListResponse,
    DocumentResponse,
    EnsureDocumentsRequest,
    EnsureDocumentsResponse,
    GenerationRunResponse,
)

router = APIRouter(tags=["documents"])


@router.post("/internal/generations", response_model=GenerationRunResponse)
async def create_generation(
    request: CreateDocumentRequest, db: Session = Depends(get_db)
) -> GenerationRunResponse:
    return DocumentService(db).create_generation_request(request)


@router.post("/internal/generations/ensure", response_model=EnsureDocumentsResponse)
async def ensure_documents(
    request: EnsureDocumentsRequest, db: Session = Depends(get_db)
) -> EnsureDocumentsResponse:
    return DocumentService(db).ensure_documents(request)


@router.post("/internal/generations/{run_id}/execute", response_model=DocumentResponse)
async def execute_generation(run_id: UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    return await DocumentService(db).execute_generation(run_id)


@router.get("/internal/jobs/{job_id}/documents", response_model=DocumentListResponse)
async def list_documents(job_id: UUID, db: Session = Depends(get_db)) -> DocumentListResponse:
    return DocumentService(db).list_documents(job_id)


@router.get("/internal/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID, db: Session = Depends(get_db)) -> DocumentResponse:
    return DocumentService(db).get_document(document_id)


@router.delete("/internal/documents/{document_id}", status_code=204)
async def delete_document(document_id: UUID, db: Session = Depends(get_db)) -> None:
    DocumentService(db).delete_document(document_id)


@router.get("/internal/documents/{document_id}/preview")
async def preview_document(document_id: UUID, db: Session = Depends(get_db)) -> HTMLResponse:
    html = DocumentService(db).build_document_preview(document_id)
    return HTMLResponse(content=html)


@router.get("/internal/documents/{document_id}/download")
async def download_document(document_id: UUID, db: Session = Depends(get_db)) -> FileResponse:
    document = DocumentService(db).get_document(document_id)
    return FileResponse(
        path=document.file_path,
        filename=document.file_path.split("/")[-1],
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
