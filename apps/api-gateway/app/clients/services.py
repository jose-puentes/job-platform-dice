from shared_http import build_async_client

from app.core.config import settings


def job_service_client():
    return build_async_client(settings.job_service_url)


def orchestrator_service_client():
    return build_async_client(settings.orchestrator_service_url)


def ai_service_client():
    return build_async_client(settings.ai_service_url, timeout=120.0)


def apply_service_client():
    return build_async_client(settings.apply_service_url, timeout=120.0)
