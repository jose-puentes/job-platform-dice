import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from redis import asyncio as redis_async

from app.clients.services import orchestrator_service_client
from app.core.config import settings
from shared_events import SCRAPE_RUN_EVENTS_CHANNEL
from shared_types import CreateScrapeRunRequest, ScrapeRunListResponse, ScrapeRunResponse

router = APIRouter(prefix="/api/v1/scrape-runs", tags=["scrape-runs"])


@router.post("", response_model=ScrapeRunResponse)
async def create_scrape_run(request: CreateScrapeRunRequest) -> ScrapeRunResponse:
    async with orchestrator_service_client() as client:
        response = await client.post("/internal/scrape-runs", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return ScrapeRunResponse.model_validate(response.json())


@router.get("", response_model=ScrapeRunListResponse)
async def list_scrape_runs() -> ScrapeRunListResponse:
    async with orchestrator_service_client() as client:
        response = await client.get("/internal/scrape-runs")
        response.raise_for_status()
        return ScrapeRunListResponse.model_validate(response.json())


@router.get("/stream")
async def stream_scrape_runs(request: Request) -> StreamingResponse:
    async def event_stream():
        redis = redis_async.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(SCRAPE_RUN_EVENTS_CHANNEL)

        try:
            yield "event: connected\ndata: {\"status\":\"ok\"}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=15.0)
                if message and message.get("type") == "message":
                    payload = message.get("data")
                    if isinstance(payload, str):
                        event = json.loads(payload)
                        yield (
                            f"event: {event['event_type']}\n"
                            f"id: {event['event_id']}\n"
                            f"data: {payload}\n\n"
                        )
                    continue

                yield ": keepalive\n\n"
                await asyncio.sleep(0)
        finally:
            await pubsub.unsubscribe(SCRAPE_RUN_EVENTS_CHANNEL)
            await pubsub.close()
            await redis.aclose()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{run_id}", response_model=ScrapeRunResponse)
async def get_scrape_run(run_id: UUID) -> ScrapeRunResponse:
    async with orchestrator_service_client() as client:
        response = await client.get(f"/internal/scrape-runs/{run_id}")
        response.raise_for_status()
        return ScrapeRunResponse.model_validate(response.json())
