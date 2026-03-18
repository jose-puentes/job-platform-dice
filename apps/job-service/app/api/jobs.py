from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.job_service import JobCatalogService
from shared_types import JobDetail, JobIngestRequest, JobIngestResponse, JobSearchParams, PaginatedJobsResponse

router = APIRouter(prefix="/internal/jobs", tags=["jobs"])


@router.post("/ingest", response_model=JobIngestResponse)
async def ingest_jobs(request: JobIngestRequest, db: Session = Depends(get_db)) -> JobIngestResponse:
    return JobCatalogService(db).ingest_jobs(request)


@router.get("", response_model=PaginatedJobsResponse)
async def list_jobs(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    work_mode: str | None = Query(default=None),
    employment_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="posted_at_desc"),
    db: Session = Depends(get_db),
) -> PaginatedJobsResponse:
    params = JobSearchParams(
        q=q,
        source=source,
        company=company,
        location=location,
        work_mode=work_mode,
        employment_type=employment_type,
        page=page,
        page_size=page_size,
        sort=sort,
    )
    return JobCatalogService(db).list_jobs(params)


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: UUID, db: Session = Depends(get_db)) -> JobDetail:
    return JobCatalogService(db).get_job(job_id)

