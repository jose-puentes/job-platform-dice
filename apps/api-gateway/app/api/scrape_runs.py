from uuid import UUID

from fastapi import APIRouter

from app.clients.services import orchestrator_service_client
from shared_types import CreateScrapeRunRequest, ScrapeRunListResponse, ScrapeRunResponse

router = APIRouter(prefix="/api/v1/scrape-runs", tags=["scrape-runs"])


@router.post("", response_model=ScrapeRunResponse)
async def create_scrape_run(request: CreateScrapeRunRequest) -> ScrapeRunResponse:
    async with orchestrator_service_client() as client:
        response = await client.post("/internal/scrape-runs", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return ScrapeRunResponse.model_validate(response.json())


@router.get("", response_model=ScrapeRunListResponse)
async def list_scrape_runs() -> ScrapeRunListResponse:
    async with orchestrator_service_client() as client:
        response = await client.get("/internal/scrape-runs")
        response.raise_for_status()
        return ScrapeRunListResponse.model_validate(response.json())


@router.get("/{run_id}", response_model=ScrapeRunResponse)
async def get_scrape_run(run_id: UUID) -> ScrapeRunResponse:
    async with orchestrator_service_client() as client:
        response = await client.get(f"/internal/scrape-runs/{run_id}")
        response.raise_for_status()
        return ScrapeRunResponse.model_validate(response.json())

