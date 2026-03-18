from fastapi import APIRouter

from app.schemas.scrape import ScrapeExecutionRequest, ScrapeExecutionResponse
from app.services.board_base import ScrapeContext
from app.services.registry import get_adapter

router = APIRouter(prefix="/internal/scrape", tags=["scrape"])


@router.post("/execute", response_model=ScrapeExecutionResponse)
async def execute_scrape(request: ScrapeExecutionRequest) -> ScrapeExecutionResponse:
    adapter = get_adapter(request.source)
    jobs = await adapter.scrape(
        ScrapeContext(
            source=request.source,
            query=request.query,
            location=request.location,
            page_number=request.page_number,
        )
    )
    return ScrapeExecutionResponse(
        jobs=jobs,
        diagnostics=[{"adapter": adapter.name, "status": "ok"}],
    )
