import json

from redis import Redis

from app.core.config import settings
from shared_events import (
    DOCUMENT_EVENTS_CHANNEL,
    DOCUMENT_GENERATION_CREATED,
    DOCUMENT_GENERATION_UPDATED,
    EventEnvelope,
)


class DocumentEventService:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def publish_created(self, run) -> None:
        self._publish(DOCUMENT_GENERATION_CREATED, run)

    def publish_updated(self, run, document_id: str | None = None) -> None:
        self._publish(DOCUMENT_GENERATION_UPDATED, run, document_id=document_id)

    def _publish(self, event_type: str, run, document_id: str | None = None) -> None:
        payload = {
            "run": {
                "id": str(run.id),
                "job_id": str(run.job_id),
                "document_type": run.document_type.value,
                "status": run.status.value,
                "error_message": run.error_message,
                "model_name": run.model_name,
                "requested_by": run.requested_by,
            }
        }
        if document_id:
            payload["document_id"] = document_id

        envelope = EventEnvelope(
            event_type=event_type,
            correlation_id=str(run.id),
            producer="ai-service",
            payload=payload,
        )
        self.redis.publish(DOCUMENT_EVENTS_CHANNEL, json.dumps(envelope.model_dump(mode="json")))


event_service = DocumentEventService()
