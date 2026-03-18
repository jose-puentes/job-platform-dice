from app.domain.normalization import build_fingerprint, build_normalized_job


def test_build_fingerprint_is_stable() -> None:
    first = build_fingerprint("greenhouse", "123", "Acme", "Engineer", "Remote")
    second = build_fingerprint("greenhouse", "123", "Acme", "Engineer", "Remote")
    assert first == second


def test_build_normalized_job_sets_defaults() -> None:
    job = build_normalized_job(
        source_name="greenhouse",
        source_type="job_board",
        source_base_url="https://boards.greenhouse.io",
        company_name="Acme",
        title="Platform Engineer",
        description="Build things",
        job_url="https://boards.greenhouse.io/jobs/1",
    )
    assert job.source_name == "greenhouse"
    assert job.company_name == "Acme"
    assert job.fingerprint

