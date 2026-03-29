from uuid import UUID

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.clients.services import job_service_client
from shared_types import JobDetail, JobFilterMetadata, PaginatedJobsResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("", response_model=PaginatedJobsResponse)
async def list_jobs(
    q: str | None = Query(default=None),
    source: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    work_mode: str | None = Query(default=None),
    employment_type: str | None = Query(default=None),
    posted_within_days: int | None = Query(default=None, ge=1, le=365),
    salary_min: float | None = Query(default=None, ge=0),
    salary_max: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="posted_at_desc"),
) -> PaginatedJobsResponse:
    params = {
        "q": q,
        "source": source,
        "company": company,
        "location": location,
        "work_mode": work_mode,
        "employment_type": employment_type,
        "posted_within_days": posted_within_days,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "page": page,
        "page_size": page_size,
        "sort": sort,
    }
    async with job_service_client() as client:
        response = await client.get("/internal/jobs", params={k: v for k, v in params.items() if v is not None})
        response.raise_for_status()
        return PaginatedJobsResponse.model_validate(response.json())


@router.get("/filters", response_model=JobFilterMetadata)
async def get_job_filters() -> JobFilterMetadata:
    async with job_service_client() as client:
        response = await client.get("/internal/jobs/filters")
        response.raise_for_status()
        return JobFilterMetadata.model_validate(response.json())


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: UUID) -> JobDetail:
    async with job_service_client() as client:
        try:
            response = await client.get(f"/internal/jobs/{job_id}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text) from exc
        return JobDetail.model_validate(response.json())
