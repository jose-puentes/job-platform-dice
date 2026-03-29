from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.application_service import ApplicationService
from shared_types import (
    ApplicationListResponse,
    ApplicationResponse,
    ApplyAttemptPayload,
    ApplyRunExecutionPayload,
    ApplyRunResponse,
    CreateBatchApplyRequest,
    CreateSingleApplyRequest,
)

router = APIRouter(tags=["applications"])


@router.post("/internal/apply-runs/single", response_model=ApplyRunResponse)
async def create_single_apply(
    request: CreateSingleApplyRequest, db: Session = Depends(get_db)
) -> ApplyRunResponse:
    return ApplicationService(db).create_single_apply(request)


@router.post("/internal/apply-runs/batch", response_model=ApplyRunResponse)
async def create_batch_apply(
    request: CreateBatchApplyRequest, db: Session = Depends(get_db)
) -> ApplyRunResponse:
    return ApplicationService(db).create_batch_apply(request)


@router.post("/internal/apply-attempts/execute", response_model=ApplicationResponse)
async def execute_apply_attempt(
    request: ApplyAttemptPayload, db: Session = Depends(get_db)
) -> ApplicationResponse:
    return await ApplicationService(db).execute_attempt(request)


@router.post("/internal/apply-runs/execute", response_model=ApplyRunResponse)
async def execute_apply_run(
    request: ApplyRunExecutionPayload, db: Session = Depends(get_db)
) -> ApplyRunResponse:
    return await ApplicationService(db).execute_run(request)


@router.get("/internal/apply-runs", response_model=list[ApplyRunResponse])
async def list_apply_runs(db: Session = Depends(get_db)) -> list[ApplyRunResponse]:
    return ApplicationService(db).list_runs()


@router.get("/internal/apply-runs/{run_id}", response_model=ApplyRunResponse)
async def get_apply_run(run_id: UUID, db: Session = Depends(get_db)) -> ApplyRunResponse:
    return ApplicationService(db).get_run(run_id)


@router.get("/internal/applications", response_model=ApplicationListResponse)
async def list_applications(db: Session = Depends(get_db)) -> ApplicationListResponse:
    return ApplicationService(db).list_applications()


@router.get("/internal/applications/{application_id}", response_model=ApplicationResponse)
async def get_application(application_id: UUID, db: Session = Depends(get_db)) -> ApplicationResponse:
    return ApplicationService(db).get_application(application_id)


@router.get("/internal/jobs/{job_id}/application", response_model=ApplicationResponse)
async def get_latest_application_for_job(job_id: UUID, db: Session = Depends(get_db)) -> ApplicationResponse:
    return ApplicationService(db).get_latest_application_for_job(job_id)
