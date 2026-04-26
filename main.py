import asyncio
import sys
import webbrowser
from pathlib import Path
from loguru import logger
import uvicorn

from core.config import config
from core.database import init_db, reset_stuck_applying_jobs
from core.notifier import notify
from core.scheduler import setup_scheduler


def _configure_logging():
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(sys.stderr, level="INFO", colorize=True,
               format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
    logger.add(config.LOGS_DIR / "scraper.log", level="DEBUG", rotation="10 MB",
               filter=lambda r: r["extra"].get("module", "") in ("naukri", "linkedin", "indeed", "internshala"))
    logger.add(config.LOGS_DIR / "errors.log", level="ERROR", rotation="10 MB")
    logger.add(config.LOGS_DIR / "applicator.log", level="DEBUG", rotation="10 MB",
               filter=lambda r: "apply" in r["message"].lower())


def _check_env():
    missing = []
    if not config.ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY (AI scoring disabled)")
    if not config.GMAIL_ADDRESS:
        missing.append("GMAIL_ADDRESS (cold emails disabled)")
    if missing:
        logger.warning("Optional env vars not set: " + ", ".join(missing))


async def full_system_check():
    logger.info("Running startup system check...")

    # Ensure all directories exist
    for d in [config.DATA_DIR, config.LOGS_DIR, config.SESSIONS_DIR, config.RESUME_TAILORED_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Initialise DB
    await init_db()

    # Crash recovery: reset any stuck APPLYING jobs
    await reset_stuck_applying_jobs()

    # Check profile
    if not config.PROFILE_PATH.exists():
        logger.warning(f"Profile not found at {config.PROFILE_PATH} — copy profile.json.example")

    # Check resume
    if not config.RESUME_BASE_PATH.exists():
        logger.warning(f"Resume not found at {config.RESUME_BASE_PATH} — add your PDF")

    _check_env()
    logger.info("System check complete")


async def _run_initial_scrape():
    """Fire one scrape immediately on startup so the dashboard has jobs fast."""
    from scrapers.scraper_registry import run_all_scrapers
    from intelligence.job_scorer import score_pending_jobs
    logger.info("Initial scrape starting...")
    await run_all_scrapers()
    await score_pending_jobs()


async def main():
    _configure_logging()
    logger.info("=" * 50)
    logger.info(" JobHunterX starting up")
    logger.info("=" * 50)

    await full_system_check()

    # Set up and start scheduler
    scheduler = setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    notify("JobHunterX", "System started — hunting jobs now!")

    # Run initial scrape in background so API is up immediately
    asyncio.create_task(_run_initial_scrape())

    # Open dashboard
    dashboard_url = f"http://localhost:{config.DASHBOARD_PORT}"
    logger.info(f"Dashboard: {dashboard_url}")
    webbrowser.open(dashboard_url)

    # Start FastAPI
    from dashboard.api import app
    cfg = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=config.DASHBOARD_PORT,
        log_level="warning",
    )
    server = uvicorn.Server(cfg)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
