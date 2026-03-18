from datetime import UTC, datetime, timedelta

from app.domain.normalization import build_normalized_job
from app.services.board_base import BaseBoardAdapter, ScrapeContext
from shared_types import NormalizedJobPayload


class DemoBoardAdapter(BaseBoardAdapter):
    name = "demo"

    async def scrape(self, context: ScrapeContext) -> list[NormalizedJobPayload]:
        now = datetime.now(UTC)
        source_base_url = f"https://{context.source}.example.com"
        role = context.query or "software engineer"
        city = context.location or "Remote"

        jobs: list[NormalizedJobPayload] = []
        for idx in range(1, 3):
            external_job_id = f"{context.source}-{context.page_number}-{idx}"
            job_url = f"{source_base_url}/jobs/{external_job_id}"
            jobs.append(
                build_normalized_job(
                    source_name=context.source,
                    source_type=self.source_type,
                    source_base_url=source_base_url,
                    external_job_id=external_job_id,
                    company_name=f"{context.source.title()} Labs {idx}",
                    company_website=f"https://company{idx}.example.com",
                    title=f"{role.title()} {idx}",
                    location=city,
                    city=city if city != "Remote" else None,
                    work_mode="remote" if city == "Remote" else "hybrid",
                    employment_type="full_time",
                    posted_at=now - timedelta(days=idx),
                    description=f"Sample normalized job from {context.source} page {context.page_number}, listing {idx}.",
                    short_description=f"Sample {role} opportunity",
                    application_url=f"{job_url}/apply",
                    job_url=job_url,
                    raw_payload_url=job_url,
                )
            )
        return jobs

