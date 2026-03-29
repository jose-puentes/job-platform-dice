from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import EmploymentType, Job, WorkMode
from app.repositories.job_repository import JobRepository
from shared_types import (
    JobDetail,
    JobFilterMetadata,
    JobIngestRequest,
    JobIngestResponse,
    JobSearchParams,
    JobSummary,
    PaginatedJobsResponse,
)


class JobCatalogService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = JobRepository(db)

    def ingest_jobs(self, request: JobIngestRequest) -> JobIngestResponse:
        inserted = 0
        updated = 0
        duplicates = 0

        for payload in request.jobs:
            source = self.repository.get_or_create_source(payload)
            company = self.repository.get_or_create_company(payload)
            existing = self.repository.find_existing_job(str(source.id), payload)

            if existing:
                duplicates += 1
                self._update_job(existing, company_id=company.id, source_id=source.id, payload=payload)
                updated += 1
            else:
                job = Job(
                    source_id=source.id,
                    external_job_id=payload.external_job_id,
                    company_id=company.id,
                    title=payload.title,
                    location=payload.location,
                    country=payload.country,
                    state=payload.state,
                    city=payload.city,
                    work_mode=WorkMode(payload.work_mode),
                    employment_type=EmploymentType(payload.employment_type),
                    salary_min=payload.salary_min,
                    salary_max=payload.salary_max,
                    currency=payload.currency,
                    posted_at=payload.posted_at,
                    description=payload.description,
                    short_description=payload.short_description,
                    application_url=payload.application_url,
                    job_url=payload.job_url,
                    fingerprint=payload.fingerprint,
                    first_seen_at=payload.first_seen_at,
                    last_seen_at=payload.last_seen_at,
                    is_active=True,
                )
                self.db.add(job)
                inserted += 1

        self.db.commit()
        return JobIngestResponse(
            inserted=inserted,
            updated=updated,
            duplicates=duplicates,
            total_received=len(request.jobs),
        )

    def list_jobs(self, params: JobSearchParams) -> PaginatedJobsResponse:
        jobs, total = self.repository.list_jobs(params)
        return PaginatedJobsResponse(
            items=[self._to_summary(job) for job in jobs],
            page=params.page,
            page_size=params.page_size,
            total=total,
        )

    def get_job(self, job_id: UUID) -> JobDetail:
        job = self.repository.get_job(str(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return self._to_detail(job)

    def archive_job(self, job_id: UUID) -> JobDetail:
        job = self.repository.archive_job(str(job_id))
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        self.db.commit()
        return self._to_detail(job)

    def get_filter_metadata(self) -> JobFilterMetadata:
        return self.repository.get_filter_metadata()

    @staticmethod
    def _update_job(job: Job, company_id: UUID, source_id: UUID, payload) -> None:
        job.source_id = source_id
        job.company_id = company_id
        job.external_job_id = payload.external_job_id
        job.title = payload.title
        job.location = payload.location
        job.country = payload.country
        job.state = payload.state
        job.city = payload.city
        job.work_mode = WorkMode(payload.work_mode)
        job.employment_type = EmploymentType(payload.employment_type)
        job.salary_min = payload.salary_min
        job.salary_max = payload.salary_max
        job.currency = payload.currency
        job.posted_at = payload.posted_at
        job.description = payload.description
        job.short_description = payload.short_description
        job.application_url = payload.application_url
        job.job_url = payload.job_url
        job.fingerprint = payload.fingerprint
        job.last_seen_at = payload.last_seen_at
        job.is_active = True

    @staticmethod
    def _to_summary(job: Job) -> JobSummary:
        return JobSummary(
            id=job.id,
            title=job.title,
            company=job.company.name,
            source=job.source.source_name,
            location=job.location,
            short_description=job.short_description or job.description[:280],
            work_mode=job.work_mode.value,
            employment_type=job.employment_type.value,
            posted_at=job.posted_at,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            currency=job.currency,
            is_active=job.is_active,
        )

    def _to_detail(self, job: Job) -> JobDetail:
        summary = self._to_summary(job)
        detail_data = summary.model_dump()
        detail_data.update(
            description=job.description,
            application_url=job.application_url,
            job_url=job.job_url,
            first_seen_at=job.first_seen_at,
            last_seen_at=job.last_seen_at,
        )
        return JobDetail(**detail_data)
