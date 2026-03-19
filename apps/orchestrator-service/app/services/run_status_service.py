from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import AdapterDiagnostic, PayloadType, RawScrapePayload, ScrapeRunStatus, ScrapeTaskStatus
from app.repositories.scrape_repository import ScrapeRepository
from shared_types import ScrapeTaskArtifactsRequest, ScrapeTaskStatusUpdateRequest


class ScrapeRunStatusService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ScrapeRepository(db)

    def update_task_status(self, request: ScrapeTaskStatusUpdateRequest) -> None:
        task = self.repository.get_task(request.scrape_task_id)
        if not task:
            return

        status = ScrapeTaskStatus(request.status)
        task.status = status
        if request.attempt_count is not None:
            task.attempt_count = request.attempt_count
        if request.error_message is not None:
            task.error_message = request.error_message

        now = datetime.now(UTC)
        if status == ScrapeTaskStatus.RUNNING:
            task.started_at = now
        if status in {ScrapeTaskStatus.COMPLETED, ScrapeTaskStatus.FAILED}:
            task.finished_at = now

        run = self.repository.get_run(task.scrape_run_id)
        if not run:
            self.db.commit()
            return

        if request.total_found:
            run.total_found += request.total_found
        if request.total_inserted:
            run.total_inserted += request.total_inserted
        if request.total_updated:
            run.total_updated += request.total_updated
        if request.total_duplicates:
            run.total_duplicates += request.total_duplicates
        if status == ScrapeTaskStatus.FAILED:
            run.total_failed += 1

        tasks = self.repository.get_tasks_for_run(run.id)
        run.completed_tasks = sum(
            1 for existing_task in tasks if existing_task.status in {ScrapeTaskStatus.COMPLETED, ScrapeTaskStatus.FAILED}
        )

        if any(existing_task.status == ScrapeTaskStatus.RUNNING for existing_task in tasks):
            run.status = ScrapeRunStatus.RUNNING
        elif all(existing_task.status == ScrapeTaskStatus.COMPLETED for existing_task in tasks):
            run.status = ScrapeRunStatus.COMPLETED
            run.finished_at = now
        elif all(existing_task.status in {ScrapeTaskStatus.COMPLETED, ScrapeTaskStatus.FAILED} for existing_task in tasks):
            run.status = ScrapeRunStatus.PARTIAL if run.total_failed > 0 else ScrapeRunStatus.COMPLETED
            run.finished_at = now
        else:
            run.status = ScrapeRunStatus.RUNNING

        self.db.commit()

    def store_task_artifacts(self, request: ScrapeTaskArtifactsRequest) -> None:
        task = self.repository.get_task(request.scrape_task_id)
        if not task:
            return

        payloads = [
            RawScrapePayload(
                scrape_task_id=request.scrape_task_id,
                source=payload.source,
                source_url=payload.source_url,
                payload_type=PayloadType(payload.payload_type),
                raw_json=payload.raw_json,
                raw_html=payload.raw_html,
            )
            for payload in request.raw_payloads
        ]
        diagnostics = [
            AdapterDiagnostic(
                scrape_task_id=request.scrape_task_id,
                adapter_name=diagnostic.adapter_name,
                severity=diagnostic.severity,
                message=diagnostic.message,
                metadata=diagnostic.metadata,
            )
            for diagnostic in request.diagnostics
        ]

        if payloads:
            self.repository.add_raw_payloads(payloads)
        if diagnostics:
            self.repository.add_diagnostics(diagnostics)
        self.db.commit()

