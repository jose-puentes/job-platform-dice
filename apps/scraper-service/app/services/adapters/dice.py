import asyncio
import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup

from app.domain.normalization import build_normalized_job
from app.services.board_base import BaseBoardAdapter, ScrapeContext
from shared_types import AdapterDiagnosticArtifact, NormalizedJobPayload, RawScrapePayloadArtifact

DICE_BASE_URL = "https://www.dice.com"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
JOB_DETAIL_LINK_RE = re.compile(
    r"""(?:href=["'](?P<href>/job-detail/[^"'?#]+)|(?P<details>https?:(?:\\/\\/|//)www\.dice\.com(?:\\/|/)job-detail(?:\\/|/)[^"'\\?#]+))""",
    re.IGNORECASE,
)
POSTED_DATE_RE = re.compile(r"Date Posted:\s*(\d{4}-\d{2}-\d{2})", re.IGNORECASE)
SALARY_RANGE_RE = re.compile(
    r"(?P<currency>USD|\$)\s*"
    r"(?P<min>\d[\d,]*(?:\.\d+)?)"
    r"(?:\s*-\s*(?P<max>\d[\d,]*(?:\.\d+)?))?",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ParsedDiceJob:
    job: NormalizedJobPayload
    raw_payload: RawScrapePayloadArtifact


def _normalize_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        normalized = re.sub(r"\s+", " ", line).strip()
        if normalized:
            lines.append(normalized)
    return lines


def _build_search_urls(query: str, page_number: int) -> list[str]:
    slug = "-".join(part for part in re.split(r"[^a-z0-9]+", query.lower()) if part)
    page_suffix = f"?page={page_number}" if page_number > 1 else ""
    fallback_page_suffix = f"&page={page_number}" if page_number > 1 else ""
    return [
        f"{DICE_BASE_URL}/jobs/q-{slug}-l-Remote-jobs{page_suffix}",
        f"{DICE_BASE_URL}/jobs?q={quote_plus(query)}&location=Remote{fallback_page_suffix}",
    ]


def _extract_job_links(search_html: str) -> list[str]:
    seen: set[str] = set()
    links: list[str] = []
    for match in JOB_DETAIL_LINK_RE.finditer(search_html):
        href = match.group("href") or match.group("details")
        if not href:
            continue
        href = href.replace("\\/", "/")
        href = html.unescape(href)
        absolute_url = urljoin(DICE_BASE_URL, href)
        if absolute_url not in seen:
            seen.add(absolute_url)
            links.append(absolute_url)
    return links


def _extract_company(soup: BeautifulSoup) -> str:
    company_heading = soup.find("h4")
    if company_heading and company_heading.get_text(strip=True):
        return company_heading.get_text(strip=True)

    og_title = soup.find("meta", attrs={"property": "og:title"})
    if og_title and og_title.get("content"):
        parts = [part.strip() for part in og_title["content"].split(" - ") if part.strip()]
        if len(parts) >= 2:
            return parts[1]
    return "Unknown Company"


def _extract_location(lines: list[str], title: str) -> str | None:
    try:
        title_index = lines.index(title)
    except ValueError:
        title_index = 0

    for line in lines[title_index + 1 : title_index + 10]:
        if "Posted" in line:
            prefix = line.split("Posted", 1)[0]
            return prefix.rstrip(" -•·").strip()
        if line.lower().startswith("remote"):
            return line
    return None


def _is_strict_remote(location: str | None) -> bool:
    if not location:
        return False

    normalized = location.strip().lower()
    return normalized in {"remote", "remote work", "100% remote", "fully remote", "remote only"}


def _extract_employment_type(lines: list[str]) -> str:
    for line in lines[:30]:
        normalized = line.strip().lower()
        if normalized in {"full time", "full-time"}:
            return "full_time"
        if normalized in {"part time", "part-time"}:
            return "part_time"
        if normalized == "contract":
            return "contract"
        if normalized == "internship":
            return "internship"
        if normalized == "third party":
            return "contract"
    return "unknown"


def _extract_posted_at(text: str) -> datetime | None:
    match = POSTED_DATE_RE.search(text)
    if not match:
        return None
    return datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=UTC)


def _extract_salary(lines: list[str]) -> tuple[float | None, float | None, str | None]:
    for line in lines[:40]:
        if "Depends on Experience" in line:
            return None, None, None

        match = SALARY_RANGE_RE.search(line)
        if not match:
            continue

        salary_min = float(match.group("min").replace(",", ""))
        salary_max_raw = match.group("max")
        salary_max = float(salary_max_raw.replace(",", "")) if salary_max_raw else None
        currency = "USD" if match.group("currency").upper() in {"USD", "$"} else match.group("currency").upper()
        return salary_min, salary_max, currency
    return None, None, None


def _extract_description(lines: list[str]) -> tuple[str, str | None]:
    start_index = None
    for idx, line in enumerate(lines):
        if line == "Summary":
            start_index = idx + 1
            break
        if line == "Job Details":
            start_index = idx + 1

    if start_index is None:
        return "No description available.", None

    description_lines: list[str] = []
    for line in lines[start_index:]:
        if line.startswith("Dice Id:"):
            break
        if line in {"Company Info", "Similar Jobs", "Create job alert"}:
            break
        description_lines.append(line)

    description = "\n".join(description_lines).strip() or "No description available."
    first_paragraph = next((line for line in description_lines if len(line) > 20), None)
    short_description = first_paragraph[:280] if first_paragraph else None
    return description, short_description


def _extract_title(soup: BeautifulSoup, lines: list[str]) -> str:
    heading = soup.find("h1")
    if heading and heading.get_text(strip=True):
        return heading.get_text(strip=True)

    for line in lines:
        if line not in {"Job Search", "Companies", "Job Details"}:
            return line
    return "Unknown Title"


def parse_dice_job(detail_html: str, detail_url: str) -> ParsedDiceJob | None:
    soup = BeautifulSoup(detail_html, "html.parser")
    text = soup.get_text("\n")
    lines = _normalize_lines(text)
    title = _extract_title(soup, lines)
    company = _extract_company(soup)
    location = _extract_location(lines, title)

    if not _is_strict_remote(location):
        return None

    employment_type = _extract_employment_type(lines)
    posted_at = _extract_posted_at(text)
    salary_min, salary_max, currency = _extract_salary(lines)
    description, short_description = _extract_description(lines)
    external_job_id = detail_url.rstrip("/").rsplit("/", 1)[-1]

    return ParsedDiceJob(
        job=build_normalized_job(
            source_name="dice",
            source_type="job_board",
            source_base_url=DICE_BASE_URL,
            external_job_id=external_job_id,
            company_name=company,
            title=title,
            location="Remote",
            work_mode="remote",
            employment_type=employment_type,
            salary_min=salary_min,
            salary_max=salary_max,
            currency=currency,
            posted_at=posted_at,
            description=description,
            short_description=short_description,
            application_url=detail_url,
            job_url=detail_url,
            raw_payload_url=detail_url,
        ),
        raw_payload=RawScrapePayloadArtifact(
            source="dice",
            source_url=detail_url,
            payload_type="detail_html",
            raw_html=detail_html,
        ),
    )


class DiceAdapter(BaseBoardAdapter):
    name = "dice"

    async def scrape_with_artifacts(
        self, context: ScrapeContext
    ) -> tuple[list[NormalizedJobPayload], list[RawScrapePayloadArtifact], list[AdapterDiagnosticArtifact]]:
        query = (context.query or "").strip()
        if not query:
            return [], [], [
                AdapterDiagnosticArtifact(
                    adapter_name=self.name,
                    severity="warning",
                    message="No keyword query provided for Dice scrape task.",
                    metadata={"page_number": context.page_number},
                )
            ]

        async with httpx.AsyncClient(headers=DEFAULT_HEADERS, timeout=30.0, follow_redirects=True) as client:
            search_html = ""
            search_url = ""
            job_links: list[str] = []

            for candidate_url in _build_search_urls(query, context.page_number):
                response = await client.get(candidate_url)
                response.raise_for_status()
                search_html = response.text
                search_url = str(response.url)
                job_links = _extract_job_links(search_html)
                if job_links:
                    break

            raw_payloads = [
                RawScrapePayloadArtifact(
                    source="dice",
                    source_url=search_url or _build_search_urls(query, context.page_number)[0],
                    payload_type="listing_html",
                    raw_html=search_html,
                )
            ]
            diagnostics = [
                AdapterDiagnosticArtifact(
                    adapter_name=self.name,
                    severity="info",
                    message="Fetched Dice listing page.",
                    metadata={
                        "query": query,
                        "page_number": context.page_number,
                        "listing_url": search_url,
                        "job_link_count": len(job_links),
                    },
                )
            ]

            if not job_links:
                diagnostics.append(
                    AdapterDiagnosticArtifact(
                        adapter_name=self.name,
                        severity="warning",
                        message="No Dice job detail links were discovered on the listing page.",
                        metadata={"query": query, "page_number": context.page_number},
                    )
                )
                return [], raw_payloads, diagnostics

            semaphore = asyncio.Semaphore(4)

            async def fetch_and_parse(detail_url: str) -> ParsedDiceJob | None:
                async with semaphore:
                    response = await client.get(detail_url)
                    response.raise_for_status()
                    return parse_dice_job(response.text, detail_url)

            parsed_results = await asyncio.gather(
                *(fetch_and_parse(url) for url in job_links),
                return_exceptions=True,
            )

        jobs: list[NormalizedJobPayload] = []
        filtered_non_remote = 0
        failed_details = 0

        for result in parsed_results:
            if isinstance(result, Exception):
                failed_details += 1
                continue
            if result is None:
                filtered_non_remote += 1
                continue
            jobs.append(result.job)
            raw_payloads.append(result.raw_payload)

        diagnostics.append(
            AdapterDiagnosticArtifact(
                adapter_name=self.name,
                severity="info",
                message="Processed Dice detail pages.",
                metadata={
                    "query": query,
                    "page_number": context.page_number,
                    "remote_jobs_kept": len(jobs),
                    "non_remote_filtered_out": filtered_non_remote,
                    "detail_fetch_failures": failed_details,
                },
            )
        )
        return jobs, raw_payloads, diagnostics

    async def scrape(self, context: ScrapeContext) -> list[NormalizedJobPayload]:
        jobs, _, _ = await self.scrape_with_artifacts(context)
        return jobs
