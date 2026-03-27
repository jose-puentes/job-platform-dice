import json

from redis import Redis

from app.core.config import settings
from shared_events import APPLY_ATTEMPT_CREATED, APPLY_ATTEMPT_UPDATED, APPLY_EVENTS_CHANNEL, EventEnvelope


class ApplyEventService:
    def __init__(self) -> None:
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True)

    def publish_created(self, run, attempt) -> None:
        self._publish(APPLY_ATTEMPT_CREATED, run, attempt)

    def publish_updated(self, run, attempt, application=None) -> None:
        self._publish(APPLY_ATTEMPT_UPDATED, run, attempt, application=application)

    def _publish(self, event_type: str, run, attempt, application=None) -> None:
        payload = {
            "apply_run": {
                "id": str(run.id),
                "mode": run.mode.value,
                "status": run.status.value,
                "completed_jobs": run.completed_jobs,
                "failed_jobs": run.failed_jobs,
                "total_jobs": run.total_jobs,
            },
            "attempt": {
                "job_id": str(attempt.job_id),
                "status": attempt.status.value,
                "strategy": attempt.strategy.value if attempt.strategy else None,
                "error_message": attempt.error_message,
            },
        }
        if application is not None:
            payload["application"] = {
                "id": str(application.id),
                "job_id": str(application.job_id),
                "application_status": application.application_status.value,
                "apply_strategy": application.apply_strategy.value,
                "external_reference": application.external_reference,
            }

        envelope = EventEnvelope(
            event_type=event_type,
            correlation_id=str(run.id),
            producer="apply-service",
            payload=payload,
        )
        self.redis.publish(APPLY_EVENTS_CHANNEL, json.dumps(envelope.model_dump(mode="json")))


event_service = ApplyEventService()
