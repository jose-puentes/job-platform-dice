from abc import ABC, abstractmethod
from dataclasses import dataclass

from shared_types import AdapterDiagnosticArtifact, NormalizedJobPayload, RawScrapePayloadArtifact


@dataclass(slots=True)
class ScrapeContext:
    source: str
    query: str | None
    location: str | None
    page_number: int


class BaseBoardAdapter(ABC):
    name: str
    source_type: str = "job_board"

    @abstractmethod
    async def scrape(self, context: ScrapeContext) -> list[NormalizedJobPayload]:
        raise NotImplementedError

    async def scrape_with_artifacts(
        self, context: ScrapeContext
    ) -> tuple[list[NormalizedJobPayload], list[RawScrapePayloadArtifact], list[AdapterDiagnosticArtifact]]:
        jobs = await self.scrape(context)
        return jobs, [], []

