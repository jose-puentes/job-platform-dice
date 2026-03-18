from shared_types import (
    CreateBatchApplyRequest,
    CreateDocumentRequest,
    CreateSingleApplyRequest,
    EnsureDocumentsRequest,
)


def test_create_document_request() -> None:
    request = CreateDocumentRequest(
        job_id="76d58be4-3c41-4fd7-a0cd-cd4de1e2c4c8",
        document_type="resume",
    )
    assert request.document_type == "resume"


def test_batch_apply_request_accepts_multiple_ids() -> None:
    request = CreateBatchApplyRequest(
        job_ids=[
            "76d58be4-3c41-4fd7-a0cd-cd4de1e2c4c8",
            "2f57ee61-4ef8-4f8f-a27c-e76441274f4f",
        ]
    )
    assert len(request.job_ids) == 2


def test_ensure_documents_request() -> None:
    request = EnsureDocumentsRequest(
        job_id="76d58be4-3c41-4fd7-a0cd-cd4de1e2c4c8",
        document_types=["resume", "cover_letter"],
    )
    assert request.document_types == ["resume", "cover_letter"]


def test_single_apply_request() -> None:
    request = CreateSingleApplyRequest(job_id="76d58be4-3c41-4fd7-a0cd-cd4de1e2c4c8")
    assert request.triggered_by == "user"
