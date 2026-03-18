from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.applications import router as applications_router
from app.api.document_download import router as document_download_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.jobs import router as jobs_router
from app.api.scrape_runs import router as scrape_runs_router
from app.core.config import settings
from shared_utils import configure_logging

configure_logging(settings.log_level)

app = FastAPI(title="Job Bot API Gateway", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(applications_router)
app.include_router(document_download_router)
app.include_router(documents_router)
app.include_router(jobs_router)
app.include_router(scrape_runs_router)
