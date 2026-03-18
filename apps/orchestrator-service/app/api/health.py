from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import settings
from app.core.db import engine
from shared_types import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthResponse)
async def live() -> HealthResponse:
    return HealthResponse(service=settings.service_name, environment=settings.environment)


@router.get("/health/ready", response_model=HealthResponse)
async def ready() -> HealthResponse:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return HealthResponse(service=settings.service_name, environment=settings.environment)
