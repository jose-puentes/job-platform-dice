import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, Text, func
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared_db import Base


class TemplateType(str, enum.Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class DocumentType(str, enum.Enum):
    RESUME = "resume"
    COVER_LETTER = "cover_letter"


class GenerationStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def enum_values(enum_cls: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    __table_args__ = {"schema": "ai"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_type: Mapped[TemplateType] = mapped_column(
        ENUM(
            TemplateType,
            name="template_type_enum",
            schema="ai",
            create_type=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GenerationRun(Base):
    __tablename__ = "generation_runs"
    __table_args__ = {"schema": "ai"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_type: Mapped[DocumentType] = mapped_column(
        ENUM(
            DocumentType,
            name="document_type_enum",
            schema="ai",
            create_type=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    status: Mapped[GenerationStatus] = mapped_column(
        ENUM(
            GenerationStatus,
            name="generation_status_enum",
            schema="ai",
            create_type=False,
            values_callable=enum_values,
        ),
        default=GenerationStatus.PENDING,
        nullable=False,
    )
    prompt_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class GeneratedDocument(Base):
    __tablename__ = "generated_documents"
    __table_args__ = (
        Index("ix_generated_documents_job_type_created", "job_id", "document_type", "created_at"),
        {"schema": "ai"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_type: Mapped[DocumentType] = mapped_column(
        ENUM(
            DocumentType,
            name="document_type_enum",
            schema="ai",
            create_type=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    prompt_template_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    generation_status: Mapped[GenerationStatus] = mapped_column(
        ENUM(
            GenerationStatus,
            name="generation_status_enum",
            schema="ai",
            create_type=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

