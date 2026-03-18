from fastapi import APIRouter

from app.core.config import settings
from shared_types import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse(service=settings.service_name, environment=settings.environment)


@router.get("/health/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    return HealthResponse(service=settings.service_name, environment=settings.environment)

