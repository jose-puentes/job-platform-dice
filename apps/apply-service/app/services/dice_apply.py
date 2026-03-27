import re
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

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


@dataclass
class ApplyAutomationResult:
    application_status: ApplicationStatus
    apply_strategy: ApplyStrategy
    external_reference: str | None
    message: str


async def execute_dice_internal_apply(
    *,
    job: dict,
    resume_path: str | None,
    cover_letter_path: str | None,
    log_step: StepLogger,
) -> ApplyAutomationResult:
    job_url = job.get("application_url") or job.get("job_url")
    if not job_url:
        raise ManualAssistRequired("No job URL available for Dice apply flow.")
    if not settings.dice_email or not settings.dice_password:
        raise ManualAssistRequired(
            "Dice credentials are not configured. Add DICE_EMAIL and DICE_PASSWORD to enable automated apply.",
            external_reference=job_url,
        )
    if not resume_path:
        raise ManualAssistRequired("Resume document is required before starting Dice apply.", external_reference=job_url)

    await log_step("dice.prepare", "Starting Dice internal apply automation.", {"url": job_url})

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=settings.browser_headless)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await _goto(page, job_url)
            await log_step("dice.open_job", "Opened Dice job detail page.", {"url": page.url})

            if await _page_has_external_apply(page):
                raise ManualAssistRequired(
                    "This Dice listing uses an external apply flow. Keeping it as manual assist.",
                    strategy=ApplyStrategy.EXTERNAL_REDIRECT,
                    external_reference=page.url,
                )

            await _login_if_needed(page, log_step)
            await _goto(page, job_url)
            await _guard_captcha(page)

            trigger = page.locator("button, a").filter(
                has_text=re.compile(r"(easy apply|apply now|apply)", re.IGNORECASE)
            )
            if await trigger.count() == 0:
                raise ManualAssistRequired(
                    "Could not find a supported Dice internal apply button on this listing.",
                    external_reference=page.url,
                )

            await trigger.first.click()
            await page.wait_for_load_state("domcontentloaded")
            await log_step("dice.start_apply", "Opened Dice apply flow.")

            await _guard_captcha(page)
            await _upload_documents(page, resume_path, cover_letter_path, log_step)
            await _reject_unknown_required_fields(page)
            await _submit_application(page, log_step)

            return ApplyAutomationResult(
                application_status=ApplicationStatus.APPLIED,
                apply_strategy=ApplyStrategy.EASY_APPLY,
                external_reference=page.url,
                message="Dice internal apply completed successfully.",
            )
        finally:
            await context.close()
            await browser.close()


async def _goto(page: Page, url: str) -> None:
    await page.goto(url, wait_until="domcontentloaded", timeout=settings.apply_browser_timeout_ms)


async def _login_if_needed(page: Page, log_step: StepLogger) -> None:
    await log_step("dice.auth_check", "Checking whether Dice login is required.")

    password_fields = page.locator("input[type='password']")
    if await password_fields.count() > 0:
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
    if "login" not in page.url:
        await _goto(page, settings.dice_login_url)

    email = page.locator("input[type='email'], input[name='email'], input#email")
    if await email.count() > 0:
        await email.first.fill(settings.dice_email or "")

    continue_button = page.locator("button, input[type='submit']").filter(
        has_text=re.compile(r"(continue|next|sign in|log in)", re.IGNORECASE)
    )
    if await continue_button.count() > 0:
        await continue_button.first.click()

    password = page.locator("input[type='password'], input[name='password']")
    if await password.count() == 0:
        await page.wait_for_timeout(1000)
        password = page.locator("input[type='password'], input[name='password']")
    if await password.count() == 0:
        raise ManualAssistRequired("Dice login page did not expose a password field.")

    await password.first.fill(settings.dice_password or "")
    submit = page.locator("button, input[type='submit']").filter(
        has_text=re.compile(r"(sign in|log in|continue)", re.IGNORECASE)
    )
    if await submit.count() == 0:
        raise ManualAssistRequired("Dice login submit control was not found.")
    await submit.first.click()
    await page.wait_for_load_state("domcontentloaded")
    await _guard_captcha(page)
    await log_step("dice.login_complete", "Dice login completed.")


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


async def _guard_captcha(page: Page) -> None:
    captcha_frames = [
        frame
        for frame in page.frames
        if "captcha" in frame.url.lower() or "recaptcha" in frame.url.lower() or "hcaptcha" in frame.url.lower()
    ]
    if captcha_frames:
        raise ManualAssistRequired(
            "Captcha detected during Dice apply flow. Falling back to manual assist for this job."
        )


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


async def _submit_application(page: Page, log_step: StepLogger) -> None:
    await log_step("dice.submit", "Submitting Dice application.")
    submit = page.locator("button, input[type='submit']").filter(
        has_text=re.compile(r"(submit|send application|apply now|finish)", re.IGNORECASE)
    )
    if await submit.count() == 0:
        raise ManualAssistRequired("Dice apply submit button was not found.")

    await submit.first.click()
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
