from shared_http import build_async_client
from shared_types import (
    JobIngestRequest,
    JobIngestResponse,
    ScrapeTaskPayload,
    ScrapeTaskStatusUpdateRequest,
)

from app.core.config import settings


async def _update_task_status(request: ScrapeTaskStatusUpdateRequest) -> None:
    async with build_async_client(settings.orchestrator_service_url) as orchestrator_client:
        response = await orchestrator_client.post(
            "/internal/scrape-tasks/status",
            json=request.model_dump(mode="json"),
        )
        response.raise_for_status()


async def execute_scrape_flow(payload: ScrapeTaskPayload) -> JobIngestResponse:
    await _update_task_status(
        ScrapeTaskStatusUpdateRequest(
            scrape_task_id=payload.scrape_task_id,
            status="running",
            attempt_count=1,
        )
    )

    async with build_async_client(settings.scraper_service_url) as scraper_client:
        scrape_response = await scraper_client.post(
            "/internal/scrape/execute",
            json=payload.model_dump(mode="json"),
        )
        scrape_response.raise_for_status()
        scrape_data = scrape_response.json()

    async with build_async_client(settings.job_service_url) as job_client:
        ingest_response = await job_client.post(
            "/internal/jobs/ingest",
            json=JobIngestRequest(jobs=scrape_data["jobs"]).model_dump(mode="json"),
        )
        ingest_response.raise_for_status()
        result = JobIngestResponse.model_validate(ingest_response.json())

    await _update_task_status(
        ScrapeTaskStatusUpdateRequest(
            scrape_task_id=payload.scrape_task_id,
            status="completed",
            attempt_count=1,
            total_found=len(scrape_data["jobs"]),
            total_inserted=result.inserted,
            total_updated=result.updated,
            total_duplicates=result.duplicates,
        )
    )
    return result
