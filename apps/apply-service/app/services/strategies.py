from app.models import ApplyStrategy


def determine_apply_strategy(job: dict) -> ApplyStrategy:
    application_url = (job.get("application_url") or "").lower()
    job_url = (job.get("job_url") or "").lower()
    source = (job.get("source") or "").lower()

    if "lever" in application_url or "greenhouse" in application_url:
        return ApplyStrategy.EXTERNAL_REDIRECT
    if source == "dice" and ("dice.com/job-detail" in application_url or "dice.com/job-detail" in job_url):
        return ApplyStrategy.EASY_APPLY
    if source in {"indeed_easy_apply", "linkedin_easy_apply"}:
        return ApplyStrategy.EASY_APPLY
    return ApplyStrategy.MANUAL_ASSIST
