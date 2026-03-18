import hashlib
from typing import cast

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Company, EmploymentType, Job, JobSource, WorkMode
from shared_types import JobSearchParams, NormalizedJobPayload


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_source(self, payload: NormalizedJobPayload) -> JobSource:
        source = self.db.execute(
            select(JobSource).where(JobSource.source_name == payload.source_name)
        ).scalar_one_or_none()
        if source:
            return source

        source = JobSource(
            source_name=payload.source_name,
            source_type=payload.source_type,
            base_url=payload.source_base_url,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def get_or_create_company(self, payload: NormalizedJobPayload) -> Company:
        normalized_name = self._normalize_text(payload.company_name)
        company = self.db.execute(
            select(Company).where(Company.normalized_name == normalized_name)
        ).scalar_one_or_none()
        if company:
            if payload.company_website and not company.website:
                company.website = payload.company_website
            return company

        company = Company(
            name=payload.company_name,
            normalized_name=normalized_name,
            website=payload.company_website,
        )
        self.db.add(company)
        self.db.flush()
        return company

    def find_existing_job(self, source_id: str, payload: NormalizedJobPayload) -> Job | None:
        if payload.external_job_id:
            existing = self.db.execute(
                select(Job).where(
                    Job.source_id == source_id,
                    Job.external_job_id == payload.external_job_id,
                )
            ).scalar_one_or_none()
            if existing:
                return existing

        existing = self.db.execute(
            select(Job).where(Job.fingerprint == payload.fingerprint)
        ).scalar_one_or_none()
        if existing:
            return existing

        fallback_key = self._fallback_fingerprint(payload)
        return self.db.execute(
            select(Job).join(Company).where(
                Company.normalized_name == self._normalize_text(payload.company_name),
                Job.title == payload.title,
                Job.location == payload.location,
                Job.posted_at == payload.posted_at,
                Job.fingerprint == fallback_key,
            )
        ).scalar_one_or_none()

    def list_jobs(self, params: JobSearchParams) -> tuple[list[Job], int]:
        stmt: Select[tuple[Job]] = select(Job).options(joinedload(Job.company), joinedload(Job.source))
        count_stmt = select(func.count(Job.id))

        filters = [Job.is_active.is_(True)]
        if params.q:
            like = f"%{params.q}%"
            filters.append(or_(Job.title.ilike(like), Job.description.ilike(like)))
        if params.company:
            filters.append(Company.normalized_name == self._normalize_text(params.company))
            stmt = stmt.join(Company)
            count_stmt = count_stmt.join(Company)
        if params.source:
            filters.append(JobSource.source_name == params.source)
            stmt = stmt.join(JobSource)
            count_stmt = count_stmt.join(JobSource)
        if params.location:
            filters.append(Job.location.ilike(f"%{params.location}%"))
        if params.work_mode:
            filters.append(Job.work_mode == WorkMode(params.work_mode))
        if params.employment_type:
            filters.append(Job.employment_type == EmploymentType(params.employment_type))

        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

        if params.sort == "posted_at_asc":
            stmt = stmt.order_by(Job.posted_at.asc().nullslast(), Job.id.asc())
        else:
            stmt = stmt.order_by(Job.posted_at.desc().nullslast(), Job.id.desc())

        total = self.db.execute(count_stmt).scalar_one()
        offset = (params.page - 1) * params.page_size
        items = self.db.execute(stmt.offset(offset).limit(params.page_size)).scalars().all()
        return items, cast(int, total)

    def get_job(self, job_id: str) -> Job | None:
        return self.db.execute(
            select(Job)
            .options(joinedload(Job.company), joinedload(Job.source))
            .where(Job.id == job_id)
        ).scalar_one_or_none()

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.lower().split())

    def _fallback_fingerprint(self, payload: NormalizedJobPayload) -> str:
        basis = "|".join(
            [
                self._normalize_text(payload.company_name),
                self._normalize_text(payload.title),
                self._normalize_text(payload.location or ""),
                payload.posted_at.date().isoformat() if payload.posted_at else "",
            ]
        )
        return hashlib.sha256(basis.encode("utf-8")).hexdigest()

