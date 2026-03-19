from app.services.adapters.dice import _extract_job_links, parse_dice_job


def test_extract_job_links_returns_unique_detail_urls() -> None:
    html = """
    <html>
      <body>
        <a href="/job-detail/abc-123">First</a>
        <a href="/job-detail/abc-123">Duplicate</a>
        <a href="/job-detail/xyz-789">Second</a>
      </body>
    </html>
    """

    links = _extract_job_links(html)

    assert links == [
        "https://www.dice.com/job-detail/abc-123",
        "https://www.dice.com/job-detail/xyz-789",
    ]


def test_parse_dice_job_keeps_strict_remote_roles() -> None:
    html = """
    <html>
      <head>
        <title>Senior Python Engineer - Example Co - Remote | Dice.com</title>
      </head>
      <body>
        <h1>Senior Python Engineer</h1>
        <div>Remote • Posted 30+ days ago • Updated 7 days ago</div>
        <div>Full Time</div>
        <div>USD 120,000.00 - 150,000.00 per year</div>
        <h4>Example Co</h4>
        <div>Job Details</div>
        <div>Summary</div>
        <div>Build remote Python systems.</div>
        <div>Date Posted: 2026-03-16</div>
        <div>Dice Id: 123</div>
      </body>
    </html>
    """

    parsed = parse_dice_job(html, "https://www.dice.com/job-detail/abc-123")

    assert parsed is not None
    assert parsed.job.company_name == "Example Co"
    assert parsed.job.work_mode == "remote"
    assert parsed.job.employment_type == "full_time"
    assert parsed.job.salary_min == 120000.0
    assert parsed.job.salary_max == 150000.0


def test_parse_dice_job_filters_remote_or_hybrid_roles() -> None:
    html = """
    <html>
      <body>
        <h1>Senior Python Engineer</h1>
        <div>Remote or Dallas, Texas • Today</div>
        <h4>Example Co</h4>
        <div>Summary</div>
        <div>Hybrid leaning role.</div>
      </body>
    </html>
    """

    parsed = parse_dice_job(html, "https://www.dice.com/job-detail/abc-123")

    assert parsed is None
