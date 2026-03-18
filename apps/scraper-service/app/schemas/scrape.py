from pydantic import BaseModel

from shared_types import NormalizedJobPayload, ScrapeTaskPayload


class ScrapeExecutionRequest(ScrapeTaskPayload):
    pass


class ScrapeExecutionResponse(BaseModel):
    jobs: list[NormalizedJobPayload]
    diagnostics: list[dict[str, str]] = []

