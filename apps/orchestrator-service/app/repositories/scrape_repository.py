from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AdapterDiagnostic, RawScrapePayload, ScrapeRun, ScrapeTask


class ScrapeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_run(self, run: ScrapeRun) -> ScrapeRun:
        self.db.add(run)
        self.db.flush()
        return run

    def add_tasks(self, tasks: list[ScrapeTask]) -> list[ScrapeTask]:
        self.db.add_all(tasks)
        self.db.flush()
        return tasks

    def add_raw_payloads(self, payloads: list[RawScrapePayload]) -> list[RawScrapePayload]:
        self.db.add_all(payloads)
        self.db.flush()
        return payloads

    def add_diagnostics(self, diagnostics: list[AdapterDiagnostic]) -> list[AdapterDiagnostic]:
        self.db.add_all(diagnostics)
        self.db.flush()
        return diagnostics

    def list_runs(self) -> list[ScrapeRun]:
        return self.db.execute(select(ScrapeRun).order_by(desc(ScrapeRun.created_at))).scalars().all()

    def get_run(self, run_id: UUID) -> ScrapeRun | None:
        return self.db.execute(select(ScrapeRun).where(ScrapeRun.id == run_id)).scalar_one_or_none()

    def get_task(self, task_id: UUID) -> ScrapeTask | None:
        return self.db.execute(select(ScrapeTask).where(ScrapeTask.id == task_id)).scalar_one_or_none()

    def get_tasks_for_run(self, run_id: UUID) -> list[ScrapeTask]:
        return self.db.execute(select(ScrapeTask).where(ScrapeTask.scrape_run_id == run_id)).scalars().all()
