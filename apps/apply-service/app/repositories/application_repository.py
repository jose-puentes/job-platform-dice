from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import Application, ApplicationEvent, ApplyAttempt, ApplyRun


class ApplicationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add_run(self, run: ApplyRun) -> ApplyRun:
        self.db.add(run)
        self.db.flush()
        return run

    def add_attempts(self, attempts: list[ApplyAttempt]) -> list[ApplyAttempt]:
        self.db.add_all(attempts)
        self.db.flush()
        return attempts

    def get_run(self, run_id: UUID) -> ApplyRun | None:
        return self.db.execute(select(ApplyRun).where(ApplyRun.id == run_id)).scalar_one_or_none()

    def get_attempt(self, run_id: UUID, job_id: UUID) -> ApplyAttempt | None:
        return self.db.execute(
            select(ApplyAttempt).where(ApplyAttempt.apply_run_id == run_id, ApplyAttempt.job_id == job_id)
        ).scalar_one_or_none()

    def list_runs(self) -> list[ApplyRun]:
        return self.db.execute(select(ApplyRun).order_by(desc(ApplyRun.created_at))).scalars().all()

    def list_applications(self) -> list[Application]:
        return self.db.execute(select(Application).order_by(desc(Application.created_at))).scalars().all()

    def get_application(self, application_id: UUID) -> Application | None:
        return self.db.execute(
            select(Application).where(Application.id == application_id)
        ).scalar_one_or_none()

    def add_application(self, application: Application) -> Application:
        self.db.add(application)
        self.db.flush()
        return application

    def add_event(self, event: ApplicationEvent) -> ApplicationEvent:
        self.db.add(event)
        self.db.flush()
        return event

