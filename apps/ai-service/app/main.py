from fastapi import FastAPI

from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.core.config import settings
from shared_utils import configure_logging

configure_logging(settings.log_level)

app = FastAPI(title="AI Service", version="0.1.0")
app.include_router(health_router)
app.include_router(documents_router)
