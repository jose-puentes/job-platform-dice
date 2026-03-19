from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.run_status_service import ScrapeRunStatusService
from shared_types import ScrapeTaskArtifactsRequest, ScrapeTaskStatusUpdateRequest

router = APIRouter(prefix="/internal/scrape-tasks", tags=["scrape-task-updates"])


@router.post("/status", status_code=status.HTTP_204_NO_CONTENT)
async def update_scrape_task_status(
    request: ScrapeTaskStatusUpdateRequest, db: Session = Depends(get_db)
) -> Response:
    ScrapeRunStatusService(db).update_task_status(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/artifacts", status_code=status.HTTP_204_NO_CONTENT)
async def store_scrape_task_artifacts(
    request: ScrapeTaskArtifactsRequest, db: Session = Depends(get_db)
) -> Response:
    ScrapeRunStatusService(db).store_task_artifacts(request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

