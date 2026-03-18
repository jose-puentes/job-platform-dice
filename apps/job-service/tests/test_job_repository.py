from app.repositories.job_repository import JobRepository


def test_normalize_text() -> None:
    assert JobRepository._normalize_text("  Senior   Engineer ") == "senior engineer"
