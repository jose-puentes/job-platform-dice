import json
from uuid import uuid4

from redis import Redis

from app.core.config import settings
from shared_events import EventEnvelope, SCRAPE_RUN_CREATED, SCRAPE_RUN_EVENTS_CHANNEL, SCRAPE_RUN_UPDATED
from shared_types import ScrapeRunResponse


class ScrapeRunEventService:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def publish_created(self, run: ScrapeRunResponse) -> None:
        self._publish(SCRAPE_RUN_CREATED, run)

    def publish_updated(self, run: ScrapeRunResponse) -> None:
        self._publish(SCRAPE_RUN_UPDATED, run)

    def _publish(self, event_type: str, run: ScrapeRunResponse) -> None:
        envelope = EventEnvelope(
            event_type=event_type,
            correlation_id=str(run.id),
            producer="orchestrator-service",
            payload={"run": run.model_dump(mode="json")},
        )
        self.redis.publish(SCRAPE_RUN_EVENTS_CHANNEL, json.dumps(envelope.model_dump(mode="json")))


event_service = ScrapeRunEventService()
