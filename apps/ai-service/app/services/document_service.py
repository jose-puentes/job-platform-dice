from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import DocumentType, GenerationStatus, PromptTemplate, TemplateType
from app.core.queue import celery_app
from app.repositories.document_repository import DocumentRepository
from app.services.docx_builder import build_docx
from app.services.openai_client import generate_text
from app.services.prompt_templates import DEFAULT_TEMPLATES
from shared_http import build_async_client
from shared_types import (
    CreateDocumentRequest,
    DocumentListResponse,
    DocumentResponse,
    EnsureDocumentsRequest,
    EnsureDocumentsResponse,
    GenerationRunResponse,
)
from app.core.config import settings


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DocumentRepository(db)

    def ensure_default_templates(self) -> None:
        changed = False
        for key, content in DEFAULT_TEMPLATES.items():
            template_type = TemplateType.RESUME if key == "resume" else TemplateType.COVER_LETTER
            existing = self.repository.get_active_template(template_type)
            if existing:
                continue
            self.repository.add_template(
                PromptTemplate(
                    template_type=template_type,
                    name=f"default_{key}",
                    content=content,
                    version=1,
                    is_active=True,
                )
            )
            changed = True
        if changed:
            self.db.commit()

    def create_generation_request(self, request: CreateDocumentRequest) -> GenerationRunResponse:
        self.ensure_default_templates()
        doc_type = DocumentType(request.document_type)
        template = self._get_template_for_document_type(doc_type)
        run = self.repository.create_generation_run(
            job_id=request.job_id,
            document_type=doc_type,
            prompt_template_id=template.id,
            model_name=settings.openai_model,
            requested_by=request.requested_by,
        )
        self.db.commit()
        celery_app.send_task(
            "worker.execute_document_generation",
            kwargs={"run_id": str(run.id)},
            queue="ai.generate",
        )
        return self._to_generation_response(run)

    def ensure_documents(self, request: EnsureDocumentsRequest) -> EnsureDocumentsResponse:
        self.ensure_default_templates()
        documents: list[DocumentResponse] = []
        queued_runs: list[GenerationRunResponse] = []

        for raw_document_type in request.document_types:
            document_type = DocumentType(raw_document_type)
            existing = self.repository.get_latest_completed_document(request.job_id, document_type)
            if existing:
                documents.append(self._to_document_response(existing))
                continue

            template = self._get_template_for_document_type(document_type)
            run = self.repository.create_generation_run(
                job_id=request.job_id,
                document_type=document_type,
                prompt_template_id=template.id,
                model_name=settings.openai_model,
                requested_by=request.requested_by,
            )
            queued_runs.append(self._to_generation_response(run))

        self.db.commit()
        return EnsureDocumentsResponse(documents=documents, queued_runs=queued_runs)

    async def execute_generation(self, run_id: UUID) -> DocumentResponse:
        run = self.repository.get_generation_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Generation run not found")

        run.status = GenerationStatus.RUNNING
        self.db.commit()

        try:
            template = self.repository.get_active_template(
                TemplateType.RESUME if run.document_type == DocumentType.RESUME else TemplateType.COVER_LETTER
            )
            if not template:
                raise HTTPException(status_code=500, detail="Prompt template missing")

            async with build_async_client(settings.job_service_url) as client:
                response = await client.get(f"/internal/jobs/{run.job_id}")
                response.raise_for_status()
                job = response.json()

            prompt = self._build_prompt(template.content, job)
            generated_text = generate_text(prompt)
            file_name = f"{run.job_id}_{run.document_type.value}_{run.id}.docx"
            file_path = str(Path(settings.document_storage_path) / file_name)
            build_docx(file_path, f"{run.document_type.value.replace('_', ' ').title()} for {job['title']}", generated_text)

            document = self.repository.create_document(
                job_id=run.job_id,
                document_type=run.document_type,
                prompt_template_id=run.prompt_template_id,
                model_name=run.model_name,
                file_path=file_path,
                status=GenerationStatus.COMPLETED,
                metadata={"prompt_template_id": str(run.prompt_template_id)},
            )
            run.status = GenerationStatus.COMPLETED
            self.db.commit()
            return self._to_document_response(document)
        except Exception as exc:
            run.status = GenerationStatus.FAILED
            run.error_message = str(exc)
            self.db.commit()
            raise

    def list_documents(self, job_id: UUID) -> DocumentListResponse:
        return DocumentListResponse(
            items=[self._to_document_response(document) for document in self.repository.list_documents_for_job(job_id)]
        )

    def get_document(self, document_id: UUID) -> DocumentResponse:
        document = self.repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return self._to_document_response(document)

    def _get_template_for_document_type(self, document_type: DocumentType) -> PromptTemplate:
        template_type = TemplateType.RESUME if document_type == DocumentType.RESUME else TemplateType.COVER_LETTER
        template = self.repository.get_active_template(template_type)
        if not template:
            raise HTTPException(status_code=500, detail=f"Active template missing for {document_type.value}")
        return template

    @staticmethod
    def _build_prompt(template: str, job: dict) -> str:
        return (
            f"{template}\n\n"
            f"Job title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job.get('location')}\n"
            f"Description:\n{job['description']}\n"
        )

    @staticmethod
    def _to_generation_response(run) -> GenerationRunResponse:
        return GenerationRunResponse(
            id=run.id,
            job_id=run.job_id,
            document_type=run.document_type.value,
            status=run.status.value,
            model_name=run.model_name,
            requested_by=run.requested_by,
            error_message=run.error_message,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _to_document_response(document) -> DocumentResponse:
        return DocumentResponse(
            id=document.id,
            job_id=document.job_id,
            document_type=document.document_type.value,
            generation_status=document.generation_status.value,
            file_path=document.file_path,
            model_name=document.model_name,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )
