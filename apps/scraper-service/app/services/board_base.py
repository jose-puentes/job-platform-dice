from abc import ABC, abstractmethod
from dataclasses import dataclass

from shared_types import NormalizedJobPayload


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

