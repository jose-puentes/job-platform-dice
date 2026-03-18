from celery import Celery


def build_celery_app(service_name: str, redis_url: str) -> Celery:
    app = Celery(service_name, broker=redis_url, backend=redis_url)
    app.conf.update(
        task_default_queue=f"{service_name}.default",
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_track_started=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        broker_connection_retry_on_startup=True,
    )
    return app
