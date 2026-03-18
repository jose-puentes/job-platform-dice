from shared_queue import build_celery_app

from app.core.config import settings

celery_app = build_celery_app("worker-service", settings.redis_url)

