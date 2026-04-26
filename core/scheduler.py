from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR

from core.config import config
from core.notifier import notify

scheduler = AsyncIOScheduler()


def _on_job_error(event):
    logger.error(f"Scheduler job failed: {event.job_id} — {event.exception}")
    notify("JobHunterX Error", f"Scheduler job failed: {event.job_id}")


def setup_scheduler() -> AsyncIOScheduler:
    from scrapers.scraper_registry import run_all_scrapers
    from intelligence.job_scorer import score_pending_jobs
    from applicators.base_applicator import process_approved_jobs
    from email_engine.email_sender import run_cold_email_batch
    from core.scheduler import _retry_failed_jobs

    scheduler.add_listener(_on_job_error, EVENT_JOB_ERROR)

    scheduler.add_job(
        run_all_scrapers, "interval", hours=config.SCRAPE_INTERVAL_HOURS,
        id="run_all_scrapers", max_instances=1, replace_existing=True,
    )
    scheduler.add_job(
        score_pending_jobs, "interval", minutes=config.SCORE_INTERVAL_MINUTES,
        id="score_pending_jobs", max_instances=1, replace_existing=True,
    )
    scheduler.add_job(
        process_approved_jobs, "interval", minutes=config.APPLY_INTERVAL_MINUTES,
        id="process_approved_jobs", max_instances=1, replace_existing=True,
    )
    scheduler.add_job(
        run_cold_email_batch, "cron", hour=config.COLD_EMAIL_HOUR,
        id="run_cold_email_batch", max_instances=1, replace_existing=True,
    )
    scheduler.add_job(
        _retry_failed_jobs, "interval", hours=config.RETRY_INTERVAL_HOURS,
        id="retry_failed_jobs", max_instances=1, replace_existing=True,
    )
    return scheduler


async def _retry_failed_jobs():
    from core.database import get_jobs_by_status, update_job_status
    from core.state_machine import JobStatus

    failed = await get_jobs_by_status(JobStatus.FAILED)
    for job in failed:
        if job["retry_count"] < config.MAX_RETRIES:
            try:
                await update_job_status(job["id"], JobStatus.APPLYING)
                logger.info(f"Queued retry for job {job['id']}: {job['title']}")
            except Exception as e:
                logger.error(f"Retry reset failed for job {job['id']}: {e}")
