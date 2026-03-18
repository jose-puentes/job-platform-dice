from uuid import UUID

from fastapi import APIRouter, Query

from app.clients.services import job_service_client
from shared_types import JobDetail, PaginatedJobsResponse

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


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
) -> PaginatedJobsResponse:
    params = {
        "q": q,
        "source": source,
        "company": company,
        "location": location,
        "work_mode": work_mode,
        "employment_type": employment_type,
        "page": page,
        "page_size": page_size,
        "sort": sort,
    }
    async with job_service_client() as client:
        response = await client.get("/internal/jobs", params={k: v for k, v in params.items() if v is not None})
        response.raise_for_status()
        return PaginatedJobsResponse.model_validate(response.json())


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: UUID) -> JobDetail:
    async with job_service_client() as client:
        response = await client.get(f"/internal/jobs/{job_id}")
        response.raise_for_status()
        return JobDetail.model_validate(response.json())

