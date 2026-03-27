from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.queue import celery_app
from app.models import (
    Application,
    ApplicationEvent,
    ApplicationStatus,
    ApplyStrategy,
    ApplyAttempt,
    ApplyAttemptStatus,
    ApplyMode,
    ApplyRun,
    ApplyRunStatus,
)
from app.repositories.application_repository import ApplicationRepository
from app.services.apply_event_service import event_service
from app.services.dice_apply import ApplyAutomationResult, ManualAssistRequired, execute_dice_internal_apply
from app.services.strategies import determine_apply_strategy
from shared_http import build_async_client
from shared_types import (
    ApplicationListResponse,
    ApplicationResponse,
    ApplyAttemptPayload,
    ApplyRunResponse,
    CreateBatchApplyRequest,
    CreateSingleApplyRequest,
    EnsureDocumentsRequest,
)
from app.core.config import settings


class ApplicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ApplicationRepository(db)

    def create_single_apply(self, request: CreateSingleApplyRequest) -> ApplyRunResponse:
        return self._create_run([request.job_id], request.triggered_by, ApplyMode.SINGLE)

    def create_batch_apply(self, request: CreateBatchApplyRequest) -> ApplyRunResponse:
        return self._create_run(request.job_ids, request.triggered_by, ApplyMode.BATCH)

    def list_runs(self) -> list[ApplyRunResponse]:
        return [self._to_run_response(run) for run in self.repository.list_runs()]

    def get_run(self, run_id: UUID) -> ApplyRunResponse:
        run = self.repository.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Apply run not found")
        return self._to_run_response(run)

    def list_applications(self) -> ApplicationListResponse:
        return ApplicationListResponse(
            items=[self._to_application_response(app) for app in self.repository.list_applications()]
        )

    def get_application(self, application_id: UUID) -> ApplicationResponse:
        application = self.repository.get_application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        return self._to_application_response(application)

    async def execute_attempt(self, payload: ApplyAttemptPayload) -> ApplicationResponse:
        run = self.repository.get_run(payload.apply_run_id)
        attempt = self.repository.get_attempt(payload.apply_run_id, payload.job_id)
        if not run or not attempt:
            raise HTTPException(status_code=404, detail="Apply attempt not found")

        attempt.status = ApplyAttemptStatus.RUNNING
        if not run.started_at:
            run.started_at = datetime.now(UTC)
        run.status = ApplyRunStatus.RUNNING
        attempt.metadata_json = {"logs": []}
        self.db.commit()
        await self._log_attempt_step(run, attempt, "apply.started", "Starting apply attempt.")

        try:
            async with build_async_client(settings.job_service_url) as client:
                job_response = await client.get(f"/internal/jobs/{payload.job_id}")
                job_response.raise_for_status()
                job = job_response.json()
            await self._log_attempt_step(run, attempt, "apply.job_loaded", "Loaded job details.", {"job_url": job.get("job_url")})

            strategy = determine_apply_strategy(job)
            attempt.strategy = strategy
            self.db.commit()
            event_service.publish_updated(run, attempt)
            await self._log_attempt_step(
                run,
                attempt,
                "apply.strategy_selected",
                f"Selected apply strategy: {strategy.value}.",
                {"strategy": strategy.value},
            )

            async with build_async_client(settings.ai_service_url, timeout=120.0) as ai_client:
                await self._log_attempt_step(run, attempt, "apply.ensure_documents", "Ensuring resume and cover letter.")
                ensure_response = await ai_client.post(
                    "/internal/generations/ensure",
                    json=EnsureDocumentsRequest(
                        job_id=payload.job_id,
                        document_types=["resume", "cover_letter"],
                        requested_by=payload.triggered_by,
                    ).model_dump(mode="json"),
                )
                ensure_response.raise_for_status()
                ensure_data = ensure_response.json()

                for run_item in ensure_data["queued_runs"]:
                    await self._log_attempt_step(
                        run,
                        attempt,
                        "apply.generate_document",
                        f"Generating {run_item['document_type'].replace('_', ' ')}.",
                        {"document_type": run_item["document_type"]},
                    )
                    execute_response = await ai_client.post(
                        f"/internal/generations/{run_item['id']}/execute"
                    )
                    execute_response.raise_for_status()

                docs_response = await ai_client.get(f"/internal/jobs/{payload.job_id}/documents")
                docs_response.raise_for_status()
                documents = docs_response.json()["items"]
            await self._log_attempt_step(run, attempt, "apply.documents_ready", "Tailored documents are ready.")

            resume_doc = next((doc for doc in documents if doc["document_type"] == "resume"), None)
            cover_doc = next((doc for doc in documents if doc["document_type"] == "cover_letter"), None)

            automation_result = await self._execute_strategy(
                strategy=strategy,
                job=job,
                resume_doc=resume_doc,
                cover_doc=cover_doc,
                run=run,
                attempt=attempt,
            )

            application = self.repository.add_application(
                Application(
                    job_id=payload.job_id,
                    application_status=automation_result.application_status,
                    apply_strategy=automation_result.apply_strategy,
                    resume_document_id=UUID(resume_doc["id"]) if resume_doc else None,
                    cover_letter_document_id=UUID(cover_doc["id"]) if cover_doc else None,
                    applied_at=datetime.now(UTC),
                    external_reference=automation_result.external_reference,
                )
            )
            self._persist_attempt_logs_as_events(application.id, attempt)
            self.repository.add_event(
                ApplicationEvent(
                    application_id=application.id,
                    event_type="apply_attempt_completed",
                    message=automation_result.message,
                    metadata_json={
                        "strategy": automation_result.apply_strategy.value,
                        "attempt_logs": attempt.metadata_json.get("logs", []),
                    },
                )
            )

            attempt.status = ApplyAttemptStatus.COMPLETED
            run.completed_jobs += 1
            if run.completed_jobs == run.total_jobs:
                run.status = ApplyRunStatus.COMPLETED
                run.finished_at = datetime.now(UTC)
            self.db.commit()
            event_service.publish_updated(run, attempt, application=application)
            return self._to_application_response(application)
        except ManualAssistRequired as exc:
            await self._log_attempt_step(
                run,
                attempt,
                "apply.manual_assist",
                str(exc),
                {"strategy": exc.strategy.value},
            )
            application = self.repository.add_application(
                Application(
                    job_id=payload.job_id,
                    application_status=ApplicationStatus.MANUAL_ASSIST,
                    apply_strategy=exc.strategy,
                    resume_document_id=UUID(resume_doc["id"]) if resume_doc else None,
                    cover_letter_document_id=UUID(cover_doc["id"]) if cover_doc else None,
                    applied_at=datetime.now(UTC),
                    external_reference=exc.external_reference or job.get("application_url") or job.get("job_url"),
                )
            )
            self._persist_attempt_logs_as_events(application.id, attempt)
            self.repository.add_event(
                ApplicationEvent(
                    application_id=application.id,
                    event_type="apply_manual_assist",
                    message=str(exc),
                    metadata_json={"attempt_logs": attempt.metadata_json.get("logs", [])},
                )
            )
            attempt.status = ApplyAttemptStatus.COMPLETED
            run.completed_jobs += 1
            if run.completed_jobs == run.total_jobs:
                run.status = ApplyRunStatus.COMPLETED
                run.finished_at = datetime.now(UTC)
            self.db.commit()
            event_service.publish_updated(run, attempt, application=application)
            return self._to_application_response(application)
        except Exception as exc:
            attempt.status = ApplyAttemptStatus.FAILED
            attempt.error_message = str(exc)
            run.failed_jobs += 1
            run.status = ApplyRunStatus.PARTIAL if run.completed_jobs > 0 else ApplyRunStatus.FAILED
            if run.completed_jobs + run.failed_jobs == run.total_jobs:
                run.finished_at = datetime.now(UTC)
            self.db.commit()
            event_service.publish_updated(run, attempt)
            raise

    async def _execute_strategy(
        self,
        *,
        strategy,
        job: dict,
        resume_doc: dict | None,
        cover_doc: dict | None,
        run: ApplyRun,
        attempt: ApplyAttempt,
    ) -> ApplyAutomationResult:
        if strategy == ApplyStrategy.EASY_APPLY and (job.get("source") or "").lower() == "dice":
            return await execute_dice_internal_apply(
                job=job,
                resume_path=resume_doc["file_path"] if resume_doc else None,
                cover_letter_path=cover_doc["file_path"] if cover_doc else None,
                log_step=lambda event_type, message, metadata=None: self._log_attempt_step(
                    run, attempt, event_type, message, metadata
                ),
            )

        if strategy.value == "easy_apply":
            return ApplyAutomationResult(
                application_status=ApplicationStatus.APPLIED,
                apply_strategy=strategy,
                external_reference=f"auto-{attempt.job_id}",
                message="Auto-apply completed successfully.",
            )

        if strategy.value == "external_redirect":
            raise ManualAssistRequired(
                "This job uses an external apply flow. Keeping it as manual assist for now.",
                strategy=strategy,
                external_reference=job.get("application_url") or job.get("job_url"),
            )

        raise ManualAssistRequired(
            "Manual assist required. Tailored documents generated and destination recorded.",
            strategy=ApplyStrategy.MANUAL_ASSIST,
            external_reference=job.get("application_url") or job.get("job_url"),
        )

    async def _log_attempt_step(
        self,
        run: ApplyRun,
        attempt: ApplyAttempt,
        event_type: str,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        logs = list(attempt.metadata_json.get("logs", []))
        logs.append(
            {
                "event_type": event_type,
                "message": message,
                "metadata": metadata or {},
                "occurred_at": datetime.now(UTC).isoformat(),
            }
        )
        attempt.metadata_json = {
            **attempt.metadata_json,
            "current_step": event_type,
            "logs": logs[-25:],
        }
        self.db.commit()
        event_service.publish_updated(run, attempt)

    def _persist_attempt_logs_as_events(self, application_id: UUID, attempt: ApplyAttempt) -> None:
        for log in attempt.metadata_json.get("logs", []):
            self.repository.add_event(
                ApplicationEvent(
                    application_id=application_id,
                    event_type=log.get("event_type", "apply.log"),
                    message=log.get("message", ""),
                    metadata_json=log.get("metadata", {}),
                )
            )

    def _create_run(self, job_ids: list[UUID], triggered_by: str, mode: ApplyMode) -> ApplyRunResponse:
        run = self.repository.add_run(
            ApplyRun(
                triggered_by=triggered_by,
                mode=mode,
                status=ApplyRunStatus.PENDING,
                total_jobs=len(job_ids),
            )
        )
        attempts = self.repository.add_attempts(
            [
                ApplyAttempt(
                    apply_run_id=run.id,
                    job_id=job_id,
                    strategy=determine_apply_strategy({}),
                    status=ApplyAttemptStatus.PENDING,
                )
                for job_id in job_ids
            ]
        )
        self.db.commit()
        for attempt in attempts:
            event_service.publish_created(run, attempt)

        for attempt in attempts:
            celery_app.send_task(
                "worker.execute_apply_task",
                kwargs={
                    "payload": ApplyAttemptPayload(
                        apply_run_id=run.id, job_id=attempt.job_id, triggered_by=triggered_by
                    ).model_dump(mode="json")
                },
                queue="apply.single" if mode == ApplyMode.SINGLE else "apply.batch",
            )

        return self._to_run_response(run)

    @staticmethod
    def _to_run_response(run: ApplyRun) -> ApplyRunResponse:
        return ApplyRunResponse(
            id=run.id,
            triggered_by=run.triggered_by,
            mode=run.mode.value,
            status=run.status.value,
            total_jobs=run.total_jobs,
            completed_jobs=run.completed_jobs,
            failed_jobs=run.failed_jobs,
            started_at=run.started_at,
            finished_at=run.finished_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _to_application_response(application: Application) -> ApplicationResponse:
        return ApplicationResponse(
            id=application.id,
            job_id=application.job_id,
            application_status=application.application_status.value,
            apply_strategy=application.apply_strategy.value,
            resume_document_id=application.resume_document_id,
            cover_letter_document_id=application.cover_letter_document_id,
            applied_at=application.applied_at,
            external_reference=application.external_reference,
            created_at=application.created_at,
            updated_at=application.updated_at,
        )
