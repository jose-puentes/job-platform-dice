import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from redis import asyncio as redis_async

from app.core.config import settings
from shared_events import APPLY_EVENTS_CHANNEL, DOCUMENT_EVENTS_CHANNEL

router = APIRouter(prefix="/api/v1/job-actions", tags=["job-actions"])


@router.get("/stream")
async def stream_job_actions(request: Request) -> StreamingResponse:
    async def event_stream():
        redis = redis_async.from_url(settings.redis_url, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.subscribe(DOCUMENT_EVENTS_CHANNEL, APPLY_EVENTS_CHANNEL)

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
            await pubsub.unsubscribe(DOCUMENT_EVENTS_CHANNEL, APPLY_EVENTS_CHANNEL)
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
