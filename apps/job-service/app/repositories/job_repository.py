import hashlib
from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import Select, distinct, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Company, EmploymentType, Job, JobSource, WorkMode
from shared_types import JobFilterMetadata, JobSearchParams, NormalizedJobPayload


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
        stmt = stmt.join(Company, Job.company_id == Company.id).join(JobSource, Job.source_id == JobSource.id)
        count_stmt = count_stmt.join(Company, Job.company_id == Company.id).join(JobSource, Job.source_id == JobSource.id)

        filters = []
        if params.q:
            like = f"%{params.q}%"
            filters.append(
                or_(
                    Job.title.ilike(like),
                    Job.description.ilike(like),
                    Job.short_description.ilike(like),
                    Company.name.ilike(like),
                )
            )
        if params.company:
            filters.append(Company.normalized_name == self._normalize_text(params.company))
        if params.source:
            filters.append(JobSource.source_name == params.source)
        if params.location:
            filters.append(Job.location.ilike(f"%{params.location}%"))
        if params.work_mode:
            filters.append(Job.work_mode == WorkMode(params.work_mode))
        if params.employment_type:
            filters.append(Job.employment_type == EmploymentType(params.employment_type))
        if params.posted_within_days:
            filters.append(Job.posted_at >= datetime.now(UTC) - timedelta(days=params.posted_within_days))

        effective_salary_min = func.coalesce(Job.salary_min, Job.salary_max)
        effective_salary_max = func.coalesce(Job.salary_max, Job.salary_min)
        if params.salary_min is not None:
            filters.append(effective_salary_max >= params.salary_min)
        if params.salary_max is not None:
            filters.append(effective_salary_min <= params.salary_max)

        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

        if params.sort == "posted_at_asc":
            stmt = stmt.order_by(Job.posted_at.asc().nullslast(), Job.id.asc())
        elif params.sort == "salary_desc":
            stmt = stmt.order_by(effective_salary_max.desc().nullslast(), Job.posted_at.desc().nullslast(), Job.id.desc())
        elif params.sort == "salary_asc":
            stmt = stmt.order_by(effective_salary_min.asc().nullslast(), Job.posted_at.desc().nullslast(), Job.id.desc())
        elif params.sort == "company_asc":
            stmt = stmt.order_by(Company.name.asc(), Job.posted_at.desc().nullslast(), Job.id.desc())
        elif params.sort == "title_asc":
            stmt = stmt.order_by(Job.title.asc(), Job.posted_at.desc().nullslast(), Job.id.desc())
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

    def get_filter_metadata(self) -> JobFilterMetadata:
        active_jobs = Job.is_active.is_(True)
        sources = self.db.execute(
            select(distinct(JobSource.source_name))
            .join(Job, Job.source_id == JobSource.id)
            .where(active_jobs)
            .order_by(JobSource.source_name.asc())
        ).scalars().all()
        companies = self.db.execute(
            select(distinct(Company.name))
            .join(Job, Job.company_id == Company.id)
            .where(active_jobs)
            .order_by(Company.name.asc())
        ).scalars().all()
        locations = self.db.execute(
            select(distinct(Job.location))
            .where(active_jobs, Job.location.is_not(None))
            .order_by(Job.location.asc())
            .limit(100)
        ).scalars().all()
        work_modes = self.db.execute(
            select(distinct(Job.work_mode))
            .where(active_jobs)
            .order_by(Job.work_mode.asc())
        ).scalars().all()
        employment_types = self.db.execute(
            select(distinct(Job.employment_type))
            .where(active_jobs)
            .order_by(Job.employment_type.asc())
        ).scalars().all()

        return JobFilterMetadata(
            sources=list(sources),
            companies=list(companies),
            locations=[location for location in locations if location],
            work_modes=[work_mode.value for work_mode in work_modes],
            employment_types=[employment_type.value for employment_type in employment_types],
        )

    def archive_job(self, job_id: str) -> Job | None:
        job = self.get_job(job_id)
        if not job:
            return None
        job.is_active = False
        return job

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
