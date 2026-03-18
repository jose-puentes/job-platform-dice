from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import DocumentType, GeneratedDocument, GenerationRun, GenerationStatus, PromptTemplate, TemplateType


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_template(self, template_type: TemplateType) -> PromptTemplate | None:
        return self.db.execute(
            select(PromptTemplate)
            .where(PromptTemplate.template_type == template_type, PromptTemplate.is_active.is_(True))
            .order_by(desc(PromptTemplate.version))
        ).scalars().first()

    def add_template(self, template: PromptTemplate) -> PromptTemplate:
        self.db.add(template)
        self.db.flush()
        return template

    def create_generation_run(
        self,
        job_id: UUID,
        document_type: DocumentType,
        prompt_template_id: UUID,
        model_name: str,
        requested_by: str,
    ) -> GenerationRun:
        run = GenerationRun(
            job_id=job_id,
            document_type=document_type,
            status=GenerationStatus.PENDING,
            prompt_template_id=prompt_template_id,
            model_name=model_name,
            requested_by=requested_by,
        )
        self.db.add(run)
        self.db.flush()
        return run

    def get_generation_run(self, run_id: UUID) -> GenerationRun | None:
        return self.db.execute(select(GenerationRun).where(GenerationRun.id == run_id)).scalar_one_or_none()

    def list_documents_for_job(self, job_id: UUID) -> list[GeneratedDocument]:
        return self.db.execute(
            select(GeneratedDocument)
            .where(GeneratedDocument.job_id == job_id)
            .order_by(desc(GeneratedDocument.created_at))
        ).scalars().all()

    def get_document(self, document_id: UUID) -> GeneratedDocument | None:
        return self.db.execute(
            select(GeneratedDocument).where(GeneratedDocument.id == document_id)
        ).scalar_one_or_none()

    def get_latest_completed_document(
        self, job_id: UUID, document_type: DocumentType
    ) -> GeneratedDocument | None:
        return self.db.execute(
            select(GeneratedDocument)
            .where(
                GeneratedDocument.job_id == job_id,
                GeneratedDocument.document_type == document_type,
                GeneratedDocument.generation_status == GenerationStatus.COMPLETED,
            )
            .order_by(desc(GeneratedDocument.created_at))
        ).scalars().first()

    def create_document(
        self,
        job_id: UUID,
        document_type: DocumentType,
        prompt_template_id: UUID,
        model_name: str,
        file_path: str,
        status: GenerationStatus,
        metadata: dict,
    ) -> GeneratedDocument:
        document = GeneratedDocument(
            job_id=job_id,
            document_type=document_type,
            prompt_template_id=prompt_template_id,
            generation_status=status,
            file_path=file_path,
            model_name=model_name,
            metadata=metadata,
        )
        self.db.add(document)
        self.db.flush()
        return document

