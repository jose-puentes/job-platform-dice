from shared_types import CreateScrapeRunRequest, JobIngestRequest, NormalizedJobPayload


def test_scrape_run_request_defaults() -> None:
    request = CreateScrapeRunRequest(source="greenhouse")
    assert request.max_pages == 1


def test_job_ingest_request_accepts_normalized_jobs() -> None:
    payload = NormalizedJobPayload(
        source_name="greenhouse",
        source_type="job_board",
        source_base_url="https://greenhouse.example.com",
        company_name="Acme",
        title="Platform Engineer",
        description="Build systems",
        job_url="https://greenhouse.example.com/job/1",
        fingerprint="abc123",
        first_seen_at="2026-03-16T00:00:00Z",
        last_seen_at="2026-03-16T00:00:00Z",
    )
    request = JobIngestRequest(jobs=[payload])
    assert len(request.jobs) == 1

