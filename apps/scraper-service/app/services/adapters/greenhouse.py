from datetime import UTC, datetime, timedelta
from urllib.parse import quote_plus

from app.domain.normalization import build_normalized_job
from app.services.board_base import BaseBoardAdapter, ScrapeContext
from shared_types import NormalizedJobPayload


class GreenhouseAdapter(BaseBoardAdapter):
    name = "greenhouse"

    async def scrape(self, context: ScrapeContext) -> list[NormalizedJobPayload]:
        # Placeholder HTTP-first implementation pattern.
        # In a full live version this would call Greenhouse board endpoints and parse JSON/HTML.
        query = context.query or "software engineer"
        location = context.location or "Remote"
        now = datetime.now(UTC)
        base_url = f"https://boards.greenhouse.io/{quote_plus(query.replace(' ', '').lower())}"

        return [
            build_normalized_job(
                source_name="greenhouse",
                source_type=self.source_type,
                source_base_url="https://boards.greenhouse.io",
                external_job_id=f"gh-{context.page_number}-1",
                company_name="Greenhouse Example Co",
                title=query.title(),
                location=location,
                work_mode="remote" if "remote" in location.lower() else "hybrid",
                employment_type="full_time",
                posted_at=now - timedelta(days=1),
                description="HTTP-first Greenhouse adapter placeholder. Replace with real endpoint parsing.",
                short_description="Greenhouse normalized role",
                application_url=f"{base_url}/apply",
                job_url=base_url,
                raw_payload_url=base_url,
            )
        ]

