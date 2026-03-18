from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.scrape_service import ScrapeOrchestratorService
from shared_types import CreateScrapeRunRequest, ScrapeRunListResponse, ScrapeRunResponse

router = APIRouter(prefix="/internal/scrape-runs", tags=["scrape-runs"])


@router.post("", response_model=ScrapeRunResponse)
async def create_scrape_run(
    request: CreateScrapeRunRequest, db: Session = Depends(get_db)
) -> ScrapeRunResponse:
    return ScrapeOrchestratorService(db).create_run(request)


@router.get("", response_model=ScrapeRunListResponse)
async def list_scrape_runs(db: Session = Depends(get_db)) -> ScrapeRunListResponse:
    return ScrapeOrchestratorService(db).list_runs()


@router.get("/{run_id}", response_model=ScrapeRunResponse)
async def get_scrape_run(run_id: UUID, db: Session = Depends(get_db)) -> ScrapeRunResponse:
    return ScrapeOrchestratorService(db).get_run(run_id)

