import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable
from urllib.parse import parse_qs, urlparse

import httpx
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import (
    FileChooser,
    Frame,
    Locator,
    Page,
    TimeoutError as PlaywrightTimeoutError,
    async_playwright,
)

from app.core.config import settings
from app.models import ApplicationStatus, ApplyStrategy

StepLogger = Callable[[str, str, dict | None], Awaitable[None]]


class ManualAssistRequired(Exception):
    def __init__(
        self,
        message: str,
        *,
        strategy: ApplyStrategy = ApplyStrategy.MANUAL_ASSIST,
        external_reference: str | None = None,
    ) -> None:
        super().__init__(message)
        self.strategy = strategy
        self.external_reference = external_reference


class JobNoLongerAvailable(Exception):
    def __init__(self, message: str, *, external_reference: str | None = None) -> None:
        super().__init__(message)
        self.external_reference = external_reference


@dataclass
class ApplyAutomationResult:
    application_status: ApplicationStatus
    apply_strategy: ApplyStrategy
    external_reference: str | None
    message: str


class DiceAutomationSession:
    def __init__(self) -> None:
        self._playwright = None
        self.browser = None
        self.context = None
        self.page: Page | None = None

    async def __aenter__(self) -> "DiceAutomationSession":
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=settings.browser_headless)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self.context is not None:
            await self.context.close()
        if self.browser is not None:
            await self.browser.close()
        if self._playwright is not None:
            await self._playwright.stop()

    async def ensure_logged_in(self, log_step: StepLogger, *, force: bool = False) -> None:
        if self.page is None:
            raise RuntimeError("DiceAutomationSession is not initialized.")

        if force:
            await log_step("dice.pre_auth", "Opening Dice login before starting apply steps.")
            await _goto(self.page, settings.dice_login_url)
            await self.page.wait_for_timeout(1500)

        if await _auth_prompt_visible(self.page):
            await _perform_login(self.page, log_step)
            return

        if force and _looks_like_login_url(self.page.url):
            await self.page.wait_for_timeout(1500)
            if await _auth_prompt_visible(self.page):
                await _perform_login(self.page, log_step)
                return
            raise ManualAssistRequired(
                "Dice login page opened, but the sign-in form did not load in a supported way."
            )

        if force:
            await log_step("dice.pre_auth_ready", "Dice session is already authenticated.")

    async def execute_apply(
        self,
        *,
        job: dict,
        resume_path: str | None,
        cover_letter_path: str | None,
        log_step: StepLogger,
    ) -> ApplyAutomationResult:
        if self.page is None:
            raise RuntimeError("DiceAutomationSession is not initialized.")

        job_url = job.get("application_url") or job.get("job_url")
        if not job_url:
            raise ManualAssistRequired("No job URL available for Dice apply flow.")
        if not settings.dice_email or not settings.dice_password:
            raise ManualAssistRequired(
                "Dice credentials are not configured. Add DICE_EMAIL and DICE_PASSWORD to enable automated apply.",
                external_reference=job_url,
            )
        if not resume_path:
            raise ManualAssistRequired(
                "Resume document is required before starting Dice apply.",
                external_reference=job_url,
            )

        await log_step(
            "dice.prepare",
            "Starting Dice internal apply automation with a login-first Dice session.",
            {"url": job_url},
        )
        await self.ensure_logged_in(log_step, force=True)

        await _goto(self.page, job_url)
        await log_step("dice.open_job", "Opened Dice job detail page.", {"url": self.page.url})

        if await _page_is_unavailable(self.page):
            raise JobNoLongerAvailable(
                "This Dice job is no longer available.",
                external_reference=self.page.url,
            )

        if await _page_has_external_apply(self.page):
            raise ManualAssistRequired(
                "This Dice listing uses an external apply flow. Keeping it as manual assist.",
                strategy=ApplyStrategy.EXTERNAL_REDIRECT,
                external_reference=self.page.url,
            )

        if await _auth_prompt_visible(self.page):
            await log_step(
                "dice.session_lost",
                "Dice still requested authentication on the job page. Re-establishing the session before apply.",
            )
            await _perform_login(self.page, log_step)
            await _goto(self.page, job_url)
        await _guard_captcha(self.page, log_step)

        wizard_url = await _resolve_dice_wizard_url(self.page, job_url)
        if wizard_url is not None:
            await _goto(self.page, wizard_url)
            await log_step(
                "dice.start_apply",
                "Opened Dice apply flow.",
                {"url": self.page.url},
            )
        else:
            await _open_apply_flow(self.page, log_step, step_name="dice.start_apply", message="Opened Dice apply flow.")

        if await _page_is_unavailable(self.page):
            raise JobNoLongerAvailable(
                "This Dice job is no longer available.",
                external_reference=self.page.url,
            )

        await _guard_captcha(self.page, log_step)
        await _ensure_authenticated_apply_flow(self.page, job_url, log_step)
        await _guard_captcha(self.page, log_step)
        await _upload_documents(self.page, resume_path, cover_letter_path, log_step)
        await _advance_dice_wizard(self.page, log_step)
        await _complete_citizenship_confirmation(self.page, log_step)
        await _reject_unknown_required_fields(self.page)
        await _submit_application(self.page, log_step)

        return ApplyAutomationResult(
            application_status=ApplicationStatus.APPLIED,
            apply_strategy=ApplyStrategy.EASY_APPLY,
            external_reference=self.page.url,
            message="Dice internal apply completed successfully.",
        )


async def execute_dice_internal_apply(
    *,
    job: dict,
    resume_path: str | None,
    cover_letter_path: str | None,
    log_step: StepLogger,
) -> ApplyAutomationResult:
    async with DiceAutomationSession() as session:
        await session.ensure_logged_in(log_step, force=True)
        return await session.execute_apply(
            job=job,
            resume_path=resume_path,
            cover_letter_path=cover_letter_path,
            log_step=log_step,
        )


async def _goto(page: Page, url: str) -> None:
    await page.goto(url, wait_until="domcontentloaded", timeout=settings.apply_browser_timeout_ms)


async def _login_if_needed(page: Page, log_step: StepLogger) -> None:
    await log_step("dice.auth_check", "Checking whether Dice login is required.")

    if await _auth_prompt_visible(page):
        await _perform_login(page, log_step)
        return

    sign_in = page.locator("a, button").filter(has_text=re.compile(r"(sign in|log in)", re.IGNORECASE))
    if await sign_in.count() > 0:
        try:
            await sign_in.first.click()
            await page.wait_for_load_state("domcontentloaded")
        except PlaywrightError:
            await _goto(page, settings.dice_login_url)
        await _perform_login(page, log_step)


async def _perform_login(page: Page, log_step: StepLogger) -> None:
    await log_step("dice.login", "Signing in to Dice.")
    auth_frame = await _wait_for_auth_frame(page)
    if auth_frame is None and "login" not in page.url:
        await _goto(page, settings.dice_login_url)
        auth_frame = await _wait_for_auth_frame(page)
    elif auth_frame is None:
        auth_frame = page.main_frame

    email = auth_frame.locator(
        "input[type='email'], input[name='email'], input#email, input[autocomplete='username'], input[name='username']"
    )
    if await email.count() == 0:
        raise ManualAssistRequired("Dice login page did not expose an email field.")
    await email.first.wait_for(state="visible", timeout=settings.apply_browser_timeout_ms)
    await email.first.fill(settings.dice_email or "")

    password = auth_frame.locator(
        "input[type='password'], input[name='password'], input[autocomplete='current-password']"
    )
    if not await _locator_has_visible_match(password):
        continue_button = auth_frame.locator("button, input[type='submit']").filter(
            has_text=re.compile(r"(continue|next)", re.IGNORECASE)
        )
        visible_continue = await _first_visible_locator(continue_button)
        if visible_continue is not None:
            await visible_continue.click()

    password = await _wait_for_password_field(page, auth_frame)
    if await password.count() == 0:
        raise ManualAssistRequired("Dice login page did not expose a password field.")

    visible_password = await _first_visible_locator(password)
    if visible_password is None:
        raise ManualAssistRequired("Dice password field did not become visible.")
    await visible_password.wait_for(state="visible", timeout=settings.apply_browser_timeout_ms)
    await visible_password.fill(settings.dice_password or "")
    submit = auth_frame.locator("button, input[type='submit']").filter(
        has_text=re.compile(r"(sign in|log in|continue)", re.IGNORECASE)
    )
    visible_submit = await _first_visible_locator(submit)
    if visible_submit is None:
        raise ManualAssistRequired("Dice login submit control was not found.")
    await visible_submit.click()
    await _wait_for_login_completion(page)
    await _guard_captcha(page, log_step)
    if await _auth_prompt_visible(page):
        raise ManualAssistRequired("Dice login did not complete successfully. The sign-in prompt is still visible.")
    await log_step("dice.login_complete", "Dice login completed.")


def _looks_like_login_url(url: str) -> bool:
    lowered = url.lower()
    return any(marker in lowered for marker in ["login", "signin", "sign-in", "auth"])


async def _wait_for_auth_frame(page: Page) -> Frame | None:
    deadline_ms = settings.apply_browser_timeout_ms
    interval_ms = 250
    waited_ms = 0

    while waited_ms < deadline_ms:
        auth_frame = await _find_auth_frame(page)
        if auth_frame is not None:
            return auth_frame
        await page.wait_for_timeout(interval_ms)
        waited_ms += interval_ms

    return await _find_auth_frame(page)


async def _wait_for_password_field(page: Page, fallback_frame: Frame) -> Locator:
    deadline_ms = settings.apply_browser_timeout_ms
    interval_ms = 250
    waited_ms = 0

    while waited_ms < deadline_ms:
        auth_frame = await _find_auth_frame(page) or fallback_frame
        password = auth_frame.locator(
            "input[type='password'], input[name='password'], input[autocomplete='current-password']"
        )
        if await _locator_has_visible_match(password):
            return password
        await page.wait_for_timeout(interval_ms)
        waited_ms += interval_ms

    return fallback_frame.locator(
        "input[type='password'], input[name='password'], input[autocomplete='current-password']"
    )


async def _wait_for_login_completion(page: Page) -> None:
    deadline_ms = settings.apply_browser_timeout_ms
    interval_ms = 300
    waited_ms = 0

    while waited_ms < deadline_ms:
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=interval_ms)
        except PlaywrightTimeoutError:
            pass

        try:
            await page.wait_for_load_state("networkidle", timeout=interval_ms)
        except PlaywrightTimeoutError:
            pass

        if await _page_has_authenticated_ui(page):
            return

        if not await _auth_prompt_visible(page) and not _looks_like_login_url(page.url):
            return

        await page.wait_for_timeout(interval_ms)
        waited_ms += interval_ms

    raise ManualAssistRequired("Dice login did not complete within the expected wait window.")


async def _ensure_authenticated_apply_flow(page: Page, job_url: str, log_step: StepLogger) -> None:
    if not await _auth_prompt_visible(page):
        return

    await log_step(
        "dice.auth_required_after_apply",
        "Dice requested authentication after opening the apply flow. Signing in and reopening the application form.",
    )
    await _perform_login(page, log_step)
    await _goto(page, job_url)
    wizard_url = await _resolve_dice_wizard_url(page, job_url)
    if wizard_url is not None:
        await _goto(page, wizard_url)
        await log_step(
            "dice.start_apply",
            "Reopened Dice apply flow after authentication.",
            {"url": page.url},
        )
        return
    await _open_apply_flow(page, log_step, step_name="dice.start_apply", message="Reopened Dice apply flow after authentication.")


async def _auth_prompt_visible(page: Page) -> bool:
    if await _find_auth_frame(page) is not None:
        return True

    auth_text_patterns = [
        r"sign in to continue",
        r"log in to continue",
        r"continue with your dice account",
        r"enter your email",
        r"enter your password",
    ]
    for frame in [page.main_frame, *page.frames]:
        try:
            body = frame.locator("body")
            if await body.count() == 0:
                continue
            text = (await body.inner_text()).lower()
        except PlaywrightError:
            continue
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in auth_text_patterns):
            return True
    return False


async def _find_auth_frame(page: Page) -> Frame | None:
    for frame in [page.main_frame, *page.frames]:
        try:
            password = frame.locator(
                "input[type='password'], input[name='password'], input[autocomplete='current-password']"
            )
            email = frame.locator(
                "input[type='email'], input[name='email'], input#email, input[autocomplete='username'], input[name='username']"
            )
            if await _locator_has_visible_match(password) or await _locator_has_visible_match(email):
                return frame
        except PlaywrightError:
            continue
    return None


async def _locator_has_visible_match(locator: Locator) -> bool:
    try:
        count = await locator.count()
    except PlaywrightError:
        return False

    for index in range(count):
        try:
            if await locator.nth(index).is_visible():
                return True
        except PlaywrightError:
            continue
    return False


async def _first_visible_locator(locator: Locator) -> Locator | None:
    try:
        count = await locator.count()
    except PlaywrightError:
        return None

    for index in range(count):
        candidate = locator.nth(index)
        try:
            if await candidate.is_visible():
                return candidate
        except PlaywrightError:
            continue
    return None


async def _page_has_authenticated_ui(page: Page) -> bool:
    auth_indicators = [
        re.compile(r"(sign out|log out|logout)", re.IGNORECASE),
        re.compile(r"(my profile|profile|account settings|dashboard)", re.IGNORECASE),
    ]
    for frame in [page.main_frame, *page.frames]:
        try:
            body = frame.locator("body")
            if await body.count() == 0:
                continue
            text = await body.inner_text()
        except PlaywrightError:
            continue
        if any(pattern.search(text) for pattern in auth_indicators):
            return True
    return False


async def _open_apply_flow(page: Page, log_step: StepLogger, *, step_name: str, message: str) -> None:
    wizard_url = await _resolve_dice_wizard_url(page, page.url)
    if wizard_url is not None:
        await _goto(page, wizard_url)
        await log_step(step_name, message, {"url": page.url})
        return

    trigger = page.locator("button, a").filter(has_text=re.compile(r"(easy apply|apply now|apply)", re.IGNORECASE))
    if await trigger.count() == 0:
        raise ManualAssistRequired(
            "Could not find a supported Dice internal apply button on this listing.",
            external_reference=page.url,
        )

    await trigger.first.click()
    await page.wait_for_load_state("domcontentloaded")
    await log_step(step_name, message)


async def _resolve_dice_wizard_url(page: Page, job_url: str) -> str | None:
    href_patterns = [
        "a[href*='/job-applications/'][href*='/wizard']",
        "[data-testid='apply-button'][href]",
        "a[href*='/wizard']",
    ]
    for selector in href_patterns:
        locator = page.locator(selector)
        try:
            count = await locator.count()
        except PlaywrightError:
            continue
        for index in range(count):
            try:
                href = await locator.nth(index).get_attribute("href")
            except PlaywrightError:
                continue
            if href and "/job-applications/" in href and "/wizard" in href:
                if href.startswith("/"):
                    parsed = urlparse(page.url or job_url)
                    return f"{parsed.scheme}://{parsed.netloc}{href}"
                return href

    try:
        html = await page.content()
    except PlaywrightError:
        html = ""

    match = re.search(r'href=[\'"](?P<href>/job-applications/[^\'"]+/wizard)[\'"]', html, re.IGNORECASE)
    if match:
        href = match.group("href")
        parsed = urlparse(page.url or job_url)
        return f"{parsed.scheme}://{parsed.netloc}{href}"

    guid_match = re.search(r"/job-detail/([0-9a-fA-F-]{36})", job_url)
    if guid_match:
        parsed = urlparse(job_url)
        return f"{parsed.scheme}://{parsed.netloc}/job-applications/{guid_match.group(1)}/wizard"

    return None


async def _page_has_external_apply(page: Page) -> bool:
    text = await page.locator("body").inner_text()
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in [
            "apply on company site",
            "apply on company website",
            "redirected to employer site",
            "external apply",
        ]
    )


async def _page_is_unavailable(page: Page) -> bool:
    text = await page.locator("body").inner_text()
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in [
            "sorry this job is no longer available",
            "this job is no longer available",
            "job is no longer available",
            "similar jobs shown below might interest you",
            "sorry, this job is no longer available",
        ]
    )


async def _guard_captcha(page: Page, log_step: StepLogger | None = None) -> None:
    if not await _captcha_present(page):
        return

    if not settings.two_captcha_api_key:
        raise ManualAssistRequired(
            "Captcha detected during Dice apply flow, and TWO_CAPTCHA_API_KEY is not configured."
        )

    site_key = await _extract_recaptcha_site_key(page)
    if not site_key:
        raise ManualAssistRequired("Captcha detected during Dice apply flow, but the reCAPTCHA site key was not found.")

    if log_step is not None:
        await log_step("dice.captcha_detected", "reCAPTCHA detected. Requesting a solve token from 2Captcha.")

    token = await _solve_recaptcha_with_twocaptcha(page.url, site_key)
    await _inject_recaptcha_token(page, token)
    await page.wait_for_timeout(1500)

    if await _captcha_present(page):
        raise ManualAssistRequired("2Captcha returned a token, but the captcha challenge is still visible.")

    if log_step is not None:
        await log_step("dice.captcha_solved", "2Captcha solved the reCAPTCHA challenge.")


async def _captcha_present(page: Page) -> bool:
    for frame in page.frames:
        lowered = frame.url.lower()
        if "captcha" in lowered or "recaptcha" in lowered or "hcaptcha" in lowered:
            return True

    selectors = [
        "iframe[src*='recaptcha']",
        ".g-recaptcha",
        "#g-recaptcha-response",
        "textarea[name='g-recaptcha-response']",
    ]
    for selector in selectors:
        locator = page.locator(selector)
        if await _locator_has_visible_match(locator):
            return True
        try:
            if await locator.count() > 0:
                return True
        except PlaywrightError:
            continue
    return False


async def _extract_recaptcha_site_key(page: Page) -> str | None:
    attr_selectors = [
        "[data-sitekey]",
        ".g-recaptcha[data-sitekey]",
        "div[data-sitekey]",
    ]
    for selector in attr_selectors:
        locator = page.locator(selector)
        try:
            count = await locator.count()
        except PlaywrightError:
            continue
        for index in range(count):
            try:
                site_key = await locator.nth(index).get_attribute("data-sitekey")
            except PlaywrightError:
                continue
            if site_key:
                return site_key

    for frame in page.frames:
        parsed = urlparse(frame.url)
        qs = parse_qs(parsed.query)
        for key_name in ("k", "sitekey", "render"):
            key = qs.get(key_name)
            if key and key[0]:
                return key[0]

    return await page.evaluate(
        """() => {
            const node = document.querySelector('[data-sitekey], .g-recaptcha');
            if (node) {
              return node.getAttribute('data-sitekey');
            }

            const scriptRegexes = [
              /sitekey['"]?\\s*[:=]\\s*['"]([^'"]+)['"]/i,
              /googlekey['"]?\\s*[:=]\\s*['"]([^'"]+)['"]/i,
              /[?&](?:k|sitekey|render)=([^&'"]+)/i,
            ];

            for (const script of Array.from(document.scripts)) {
              const text = script.textContent || script.innerHTML || '';
              for (const pattern of scriptRegexes) {
                const match = text.match(pattern);
                if (match && match[1]) {
                  return match[1];
                }
              }
            }

            for (const frame of Array.from(document.querySelectorAll('iframe[src]'))) {
              const src = frame.getAttribute('src') || '';
              for (const pattern of scriptRegexes) {
                const match = src.match(pattern);
                if (match && match[1]) {
                  return match[1];
                }
              }
            }

            return null;
        }"""
    )


async def _solve_recaptcha_with_twocaptcha(page_url: str, site_key: str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        create_response = await client.post(
            "https://2captcha.com/in.php",
            data={
                "key": settings.two_captcha_api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page_url,
                "json": 1,
            },
        )
        create_response.raise_for_status()
        create_payload = create_response.json()

        if create_payload.get("status") != 1:
            raise ManualAssistRequired(
                f"2Captcha createTask failed: {create_payload.get('request', 'unknown error')}"
            )

        request_id = create_payload["request"]
        elapsed_ms = 0
        while elapsed_ms < settings.two_captcha_timeout_ms:
            await _async_sleep(settings.two_captcha_poll_interval_ms)
            result_response = await client.get(
                "https://2captcha.com/res.php",
                params={
                    "key": settings.two_captcha_api_key,
                    "action": "get",
                    "id": request_id,
                    "json": 1,
                },
            )
            result_response.raise_for_status()
            result_payload = result_response.json()

            if result_payload.get("status") == 1:
                return result_payload["request"]
            if result_payload.get("request") != "CAPCHA_NOT_READY":
                raise ManualAssistRequired(
                    f"2Captcha solve failed: {result_payload.get('request', 'unknown error')}"
                )

            elapsed_ms += settings.two_captcha_poll_interval_ms

    raise ManualAssistRequired("2Captcha did not return a solve token within the configured timeout.")


async def _inject_recaptcha_token(page: Page, token: str) -> None:
    await page.evaluate(
        """(captchaToken) => {
            const selectors = [
              'textarea[name="g-recaptcha-response"]',
              '#g-recaptcha-response',
              'textarea[name="h-captcha-response"]',
            ];
            for (const selector of selectors) {
              const nodes = document.querySelectorAll(selector);
              nodes.forEach((node) => {
                node.value = captchaToken;
                node.innerHTML = captchaToken;
                node.dispatchEvent(new Event('input', { bubbles: true }));
                node.dispatchEvent(new Event('change', { bubbles: true }));
              });
            }

            const callCallbacks = (obj) => {
              if (!obj || typeof obj !== 'object') return;
              for (const value of Object.values(obj)) {
                if (!value) continue;
                if (typeof value === 'function') {
                  try { value(captchaToken); } catch (_) {}
                  continue;
                }
                if (typeof value === 'object') callCallbacks(value);
              }
            };

            if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {
              callCallbacks(window.___grecaptcha_cfg.clients);
            }
        }""",
        token,
    )


async def _async_sleep(milliseconds: int) -> None:
    await asyncio.sleep(milliseconds / 1000)


async def _upload_documents(
    page: Page,
    resume_path: str,
    cover_letter_path: str | None,
    log_step: StepLogger,
) -> None:
    await log_step("dice.upload_resume", "Uploading tailored resume.")
    resume_uploaded = await _set_file(page, Path(resume_path), document_kind="resume")
    if not resume_uploaded:
        await log_step(
            "dice.resume_already_attached",
            "Dice already has a resume attached for this apply flow. Reusing the existing document.",
        )

    if cover_letter_path:
        cover_uploaded = await _set_file(page, Path(cover_letter_path), document_kind="cover_letter", required=False)
        if cover_uploaded:
            await log_step("dice.upload_cover_letter", "Uploading tailored cover letter.")
        else:
            await log_step(
                "dice.cover_letter_skipped",
                "Dice apply flow did not expose a cover-letter upload control. Continuing with resume only.",
            )


async def _set_file(
    page: Page,
    path: Path,
    *,
    document_kind: str,
    required: bool = True,
) -> bool:
    input_locators = await _candidate_file_inputs(page, document_kind)
    for locator in input_locators:
        if await locator.count() == 0:
            continue
        try:
            await locator.first.set_input_files(str(path))
            return True
        except PlaywrightError:
            continue

    clicked_upload = await _try_upload_triggers(page, path, document_kind)
    if clicked_upload:
        return True

    if document_kind == "resume" and await _resume_already_attached(page):
        return False

    if required:
        raise ManualAssistRequired("Dice apply form did not expose a supported file upload control.")
    return False


async def _candidate_file_inputs(page: Page, document_kind: str) -> list[Locator]:
    frames = [page.main_frame, *page.frames]
    patterns = _document_patterns(document_kind)
    locators: list[Locator] = []

    for frame in frames:
        locators.extend(
            [
                frame.locator("input[type='file']"),
                frame.locator(
                    "label, div, button, a, span"
                ).filter(has_text=re.compile(patterns["primary"], re.IGNORECASE)),
                frame.locator(
                    "[data-testid], [data-qa], [aria-label], [name], [id]"
                ).filter(has_text=re.compile(patterns["secondary"], re.IGNORECASE)),
            ]
        )

    filtered: list[Locator] = []
    for locator in locators:
        try:
            if await locator.count() > 0:
                filtered.append(locator)
        except PlaywrightError:
            continue
    return filtered


async def _try_upload_triggers(page: Page, path: Path, document_kind: str) -> bool:
    for frame in [page.main_frame, *page.frames]:
        trigger = await _find_upload_trigger(frame, document_kind)
        if trigger is None:
            continue

        try:
            async with page.expect_file_chooser(timeout=2500) as chooser_info:
                await trigger.click()
            chooser: FileChooser = await chooser_info.value
            await chooser.set_files(str(path))
            return True
        except PlaywrightTimeoutError:
            try:
                await page.wait_for_timeout(300)
                file_inputs = frame.locator("input[type='file']")
                if await file_inputs.count() > 0:
                    await file_inputs.first.set_input_files(str(path))
                    return True
            except PlaywrightError:
                continue
        except PlaywrightError:
            continue

    return False


async def _find_upload_trigger(frame: Frame, document_kind: str) -> Locator | None:
    patterns = _document_patterns(document_kind)
    selectors = [
        frame.locator("button, a, label").filter(has_text=re.compile(patterns["primary"], re.IGNORECASE)),
        frame.get_by_text(re.compile(patterns["primary"], re.IGNORECASE)),
        frame.locator("[aria-label], [title], [data-testid], [data-qa]").filter(
            has_text=re.compile(patterns["secondary"], re.IGNORECASE)
        ),
    ]
    for locator in selectors:
        try:
            if await locator.count() > 0:
                return locator.first
        except PlaywrightError:
            continue
    return None


async def _resume_already_attached(page: Page) -> bool:
    body_text = " ".join(
        [
            (await frame.locator("body").inner_text()).lower()
            for frame in [page.main_frame, *page.frames]
            if await frame.locator("body").count() > 0
        ]
    )
    attached_markers = [
        "resume uploaded",
        "resume attached",
        "uploaded resume",
        "current resume",
        "replace resume",
        "change resume",
        "resume on file",
        "use your existing resume",
    ]
    return any(marker in body_text for marker in attached_markers)


def _document_patterns(document_kind: str) -> dict[str, str]:
    if document_kind == "cover_letter":
        return {
            "primary": r"(cover\s*letter|attach\s*cover|upload\s*cover|browse\s*cover)",
            "secondary": r"(cover|letter|attachment|attach|upload|browse|choose\s*file)",
        }
    return {
        "primary": r"(resume|upload\s*resume|attach\s*resume|browse\s*resume|cv)",
        "secondary": r"(resume|cv|attachment|attach|upload|browse|choose\s*file|replace)",
    }


async def _reject_unknown_required_fields(page: Page) -> None:
    required_inputs = page.locator(
        "input[required], textarea[required], select[required], [aria-required='true']"
    )
    unsupported = 0
    count = await required_inputs.count()
    for index in range(count):
        field = required_inputs.nth(index)
        tag_name = await field.evaluate("(node) => node.tagName.toLowerCase()")
        field_type = (await field.get_attribute("type") or "").lower()
        value = await field.input_value() if tag_name in {"input", "textarea"} else ""

        if tag_name == "input" and field_type in {"file", "hidden", "submit", "button", "checkbox", "radio"}:
            continue
        if value.strip():
            continue
        unsupported += 1

    if unsupported > 0:
        raise ManualAssistRequired(
            "Dice internal apply exposed additional required fields that are not safely auto-filled yet."
        )


async def _advance_dice_wizard(page: Page, log_step: StepLogger) -> None:
    if await _submit_control(page) is not None:
        return

    next_patterns = [
        re.compile(r"^(next|continue)$", re.IGNORECASE),
        re.compile(r"(next step|review|continue application)", re.IGNORECASE),
    ]
    for pattern in next_patterns:
        control = await _find_visible_control(page, pattern)
        if control is None:
            continue
        await log_step("dice.next_step", "Advancing to the next Dice apply step.")
        await control.click()
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        await page.wait_for_timeout(1000)
        return


async def _complete_citizenship_confirmation(page: Page, log_step: StepLogger) -> None:
    body_text = (await page.locator("body").inner_text()).lower()
    citizenship_markers = [
        "u.s. citizen",
        "us citizen",
        "citizenship",
        "authorized to work",
    ]
    if not any(marker in body_text for marker in citizenship_markers):
        return

    yes_patterns = [
        re.compile(r"^(yes|i am|confirm)$", re.IGNORECASE),
        re.compile(r"(u\.?s\.?\s*citizen|us citizen|citizenship)", re.IGNORECASE),
    ]
    for pattern in yes_patterns:
        control = await _find_visible_control(page, pattern)
        if control is None:
            continue
        try:
            await control.check()
        except Exception:
            try:
                await control.click()
            except PlaywrightError:
                continue
        await log_step("dice.citizenship_confirmed", "Confirmed the Dice citizenship step.")
        await page.wait_for_timeout(500)
        break

    if await _submit_control(page) is not None:
        return

    continue_control = await _find_visible_control(page, re.compile(r"^(next|continue)$", re.IGNORECASE))
    if continue_control is not None:
        await continue_control.click()
        try:
            await page.wait_for_load_state("networkidle", timeout=5000)
        except PlaywrightTimeoutError:
            pass
        await page.wait_for_timeout(1000)


async def _submit_application(page: Page, log_step: StepLogger) -> None:
    await log_step("dice.submit", "Submitting Dice application.")
    submit = await _submit_control(page)
    if submit is None:
        raise ManualAssistRequired("Dice apply submit button was not found.")

    await submit.click()
    try:
        await page.wait_for_load_state("networkidle", timeout=settings.apply_browser_timeout_ms)
    except PlaywrightTimeoutError:
        pass

    body_text = (await page.locator("body").inner_text()).lower()
    if any(marker in body_text for marker in ["application submitted", "you've applied", "applied successfully"]):
        await log_step("dice.completed", "Dice confirmed the application submission.")
        return

    if await _page_has_external_apply(page):
        raise ManualAssistRequired(
            "Dice apply flow redirected to an external site during submission. Switching to manual assist.",
            strategy=ApplyStrategy.EXTERNAL_REDIRECT,
            external_reference=page.url,
        )

    await log_step("dice.completed", "Dice apply flow finished without an explicit confirmation banner.")


async def _submit_control(page: Page) -> Locator | None:
    return await _find_visible_control(page, re.compile(r"(submit|send application|apply now|finish)", re.IGNORECASE))


async def _find_visible_control(page: Page, pattern: re.Pattern[str]) -> Locator | None:
    for frame in [page.main_frame, *page.frames]:
        candidates = [
            frame.locator("button, input[type='submit'], input[type='button'], a").filter(has_text=pattern),
            frame.locator("label, span, div").filter(has_text=pattern),
            frame.get_by_text(pattern),
            frame.locator(
                "[aria-label], [title], [name], [id], [data-testid], [data-qa]"
            ).filter(has_text=pattern),
        ]
        for candidate in candidates:
            visible = await _first_visible_locator(candidate)
            if visible is not None:
                return visible
    return None
