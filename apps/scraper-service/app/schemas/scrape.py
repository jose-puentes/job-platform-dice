from pydantic import BaseModel, Field

from shared_types import (
    AdapterDiagnosticArtifact,
    NormalizedJobPayload,
    RawScrapePayloadArtifact,
    ScrapeTaskPayload,
)


class ScrapeExecutionRequest(ScrapeTaskPayload):
    pass


class ScrapeExecutionResponse(BaseModel):
    jobs: list[NormalizedJobPayload]
    diagnostics: list[AdapterDiagnosticArtifact] = Field(default_factory=list)
    raw_payloads: list[RawScrapePayloadArtifact] = Field(default_factory=list)

