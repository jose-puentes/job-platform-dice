from uuid import UUID

from fastapi import APIRouter

from app.clients.services import apply_service_client
from shared_types import (
    ApplicationListResponse,
    ApplicationResponse,
    ApplyRunResponse,
    CreateBatchApplyRequest,
    CreateSingleApplyRequest,
)

router = APIRouter(tags=["applications"])


@router.post("/api/v1/jobs/{job_id}/apply", response_model=ApplyRunResponse)
async def apply_to_job(job_id: UUID) -> ApplyRunResponse:
    async with apply_service_client() as client:
        response = await client.post(
            "/internal/apply-runs/single",
            json=CreateSingleApplyRequest(job_id=job_id).model_dump(mode="json"),
        )
        response.raise_for_status()
        return ApplyRunResponse.model_validate(response.json())


@router.post("/api/v1/apply-runs", response_model=ApplyRunResponse)
async def batch_apply(request: CreateBatchApplyRequest) -> ApplyRunResponse:
    async with apply_service_client() as client:
        response = await client.post("/internal/apply-runs/batch", json=request.model_dump(mode="json"))
        response.raise_for_status()
        return ApplyRunResponse.model_validate(response.json())


@router.get("/api/v1/apply-runs", response_model=list[ApplyRunResponse])
async def list_apply_runs() -> list[ApplyRunResponse]:
    async with apply_service_client() as client:
        response = await client.get("/internal/apply-runs")
        response.raise_for_status()
        return [ApplyRunResponse.model_validate(item) for item in response.json()]


@router.get("/api/v1/apply-runs/{run_id}", response_model=ApplyRunResponse)
async def get_apply_run(run_id: UUID) -> ApplyRunResponse:
    async with apply_service_client() as client:
        response = await client.get(f"/internal/apply-runs/{run_id}")
        response.raise_for_status()
        return ApplyRunResponse.model_validate(response.json())


@router.get("/api/v1/applications", response_model=ApplicationListResponse)
async def list_applications() -> ApplicationListResponse:
    async with apply_service_client() as client:
        response = await client.get("/internal/applications")
        response.raise_for_status()
        return ApplicationListResponse.model_validate(response.json())


@router.get("/api/v1/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: UUID) -> ApplicationResponse:
    async with apply_service_client() as client:
        response = await client.get(f"/internal/applications/{application_id}")
        response.raise_for_status()
        return ApplicationResponse.model_validate(response.json())
