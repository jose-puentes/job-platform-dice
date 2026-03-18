import hashlib
from datetime import UTC, datetime

from shared_types import NormalizedJobPayload


def build_fingerprint(*parts: str) -> str:
    basis = "|".join(part.strip().lower() for part in parts if part)
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def build_normalized_job(
    *,
    source_name: str,
    source_type: str,
    source_base_url: str,
    company_name: str,
    title: str,
    description: str,
    job_url: str,
    external_job_id: str | None = None,
    company_website: str | None = None,
    location: str | None = None,
    country: str | None = None,
    state: str | None = None,
    city: str | None = None,
    work_mode: str = "unknown",
    employment_type: str = "unknown",
    salary_min: float | None = None,
    salary_max: float | None = None,
    currency: str | None = None,
    posted_at: datetime | None = None,
    short_description: str | None = None,
    application_url: str | None = None,
    raw_payload_url: str | None = None,
) -> NormalizedJobPayload:
    now = datetime.now(UTC)
    fingerprint = build_fingerprint(
        source_name,
        external_job_id or "",
        company_name,
        title,
        location or "",
        posted_at.isoformat() if posted_at else "",
    )
    return NormalizedJobPayload(
        source_name=source_name,
        source_type=source_type,
        source_base_url=source_base_url,
        external_job_id=external_job_id,
        company_name=company_name,
        company_website=company_website,
        title=title,
        location=location,
        country=country,
        state=state,
        city=city,
        work_mode=work_mode,
        employment_type=employment_type,
        salary_min=salary_min,
        salary_max=salary_max,
        currency=currency,
        posted_at=posted_at,
        description=description,
        short_description=short_description,
        application_url=application_url,
        job_url=job_url,
        fingerprint=fingerprint,
        first_seen_at=now,
        last_seen_at=now,
        raw_payload_url=raw_payload_url,
    )

