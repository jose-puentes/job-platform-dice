from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.queue import celery_app
from app.models import ScrapeRun, ScrapeRunStatus, ScrapeTask, ScrapeTaskStatus, ScrapeTaskType
from app.repositories.scrape_repository import ScrapeRepository
from shared_types import CreateScrapeRunRequest, ScrapeRunListResponse, ScrapeRunResponse, ScrapeTaskPayload


class ScrapeOrchestratorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ScrapeRepository(db)

    def create_run(self, request: CreateScrapeRunRequest) -> ScrapeRunResponse:
        queries = self._expand_queries(request.query)
        run = ScrapeRun(
            source=request.source,
            query=request.query,
            location=request.location,
            status=ScrapeRunStatus.RUNNING,
            total_tasks=request.max_pages * len(queries),
            started_at=datetime.now(UTC),
        )
        self.repository.add_run(run)

        tasks: list[ScrapeTask] = []
        for query in queries:
            for page_number in range(1, request.max_pages + 1):
                task = ScrapeTask(
                    scrape_run_id=run.id,
                    task_type=ScrapeTaskType.SEARCH_PAGE,
                    board=request.source,
                    page_number=page_number,
                    status=ScrapeTaskStatus.PENDING,
                    payload={
                        "source": request.source,
                        "query": query,
                        "location": request.location,
                        "page_number": page_number,
                    },
                )
                tasks.append(task)

        self.repository.add_tasks(tasks)
        self.db.commit()

        for task in tasks:
            celery_app.send_task(
                "worker.execute_scrape_task",
                kwargs={
                    "payload": ScrapeTaskPayload(
                        scrape_run_id=run.id,
                        scrape_task_id=task.id,
                        source=request.source,
                        query=task.payload.get("query"),
                        location=request.location,
                        page_number=task.page_number or 1,
                    ).model_dump(mode="json"),
                },
                queue="scrape.tasks",
            )

        return self._to_response(run)

    def list_runs(self) -> ScrapeRunListResponse:
        return ScrapeRunListResponse(items=[self._to_response(run) for run in self.repository.list_runs()])

    def get_run(self, run_id: UUID) -> ScrapeRunResponse:
        run = self.repository.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Scrape run not found")
        return self._to_response(run)

    @staticmethod
    def _to_response(run: ScrapeRun) -> ScrapeRunResponse:
        return ScrapeRunResponse(
            id=run.id,
            source=run.source,
            query=run.query,
            location=run.location,
            status=run.status.value,
            total_tasks=run.total_tasks,
            completed_tasks=run.completed_tasks,
            total_found=run.total_found,
            total_inserted=run.total_inserted,
            total_updated=run.total_updated,
            total_duplicates=run.total_duplicates,
            total_failed=run.total_failed,
            started_at=run.started_at,
            finished_at=run.finished_at,
            created_at=run.created_at,
            updated_at=run.updated_at,
        )

    @staticmethod
    def _expand_queries(query: str | None) -> list[str]:
        if not query:
            return [""]

        parts = [item.strip() for item in query.replace("\n", ",").replace(";", ",").split(",")]
        normalized = [item for item in parts if item]
        return normalized or [query.strip()]

