import asyncio

from shared_types import ScrapeTaskPayload

from app.core.queue import celery_app
from app.services.scrape_flow import execute_scrape_flow


@celery_app.task(name="worker.healthcheck")
def worker_healthcheck() -> str:
    return "ok"


@celery_app.task(name="worker.execute_scrape_task")
def execute_scrape_task(payload: dict) -> dict:
    task_payload = ScrapeTaskPayload.model_validate(payload)
    try:
        result = asyncio.run(execute_scrape_flow(task_payload))
        return result.model_dump(mode="json")
    except Exception as exc:
        asyncio.run(
            execute_scrape_flow_failure(task_payload, str(exc))
        )
        raise


async def execute_scrape_flow_failure(payload: ScrapeTaskPayload, error_message: str) -> None:
    from shared_http import build_async_client
    from shared_types import ScrapeTaskStatusUpdateRequest

    from app.core.config import settings

    async with build_async_client(settings.orchestrator_service_url) as orchestrator_client:
        response = await orchestrator_client.post(
            "/internal/scrape-tasks/status",
            json=ScrapeTaskStatusUpdateRequest(
                scrape_task_id=payload.scrape_task_id,
                status="failed",
                attempt_count=1,
                error_message=error_message,
            ).model_dump(mode="json"),
        )
        response.raise_for_status()


@celery_app.task(name="worker.execute_document_generation")
def execute_document_generation(run_id: str) -> dict:
    return asyncio.run(_execute_document_generation(run_id))


async def _execute_document_generation(run_id: str) -> dict:
    from shared_http import build_async_client

    from app.core.config import settings

    async with build_async_client(settings.ai_service_url, timeout=120.0) as ai_client:
        response = await ai_client.post(f"/internal/generations/{run_id}/execute")
        response.raise_for_status()
        return response.json()


@celery_app.task(name="worker.execute_apply_task")
def execute_apply_task(payload: dict) -> dict:
    return asyncio.run(_execute_apply_task(payload))


async def _execute_apply_task(payload: dict) -> dict:
    from shared_http import build_async_client

    from app.core.config import settings

    async with build_async_client(settings.apply_service_url, timeout=180.0) as apply_client:
        response = await apply_client.post("/internal/apply-attempts/execute", json=payload)
        response.raise_for_status()
        return response.json()
