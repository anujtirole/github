import asyncio
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from core.config import config
from applicators.base_applicator import BaseApplicator


class LinkedInApplicator(BaseApplicator):
    platform = "linkedin"

    async def apply(self, job: dict) -> bool:
        session_path = config.SESSIONS_DIR / "linkedin_cookies.json"
        if not session_path.exists():
            logger.error("[linkedin_apply] No session file — run setup_sessions.py")
            return False
        if not job.get("job_url"):
            return False
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(storage_state=str(session_path))
                page = await ctx.new_page()
                await page.goto(job["job_url"], timeout=25000)
                await asyncio.sleep(2)

                easy_apply = await page.query_selector(
                    "button.jobs-apply-button:has-text('Easy Apply')"
                )
                if not easy_apply:
                    logger.info(f"[linkedin_apply] No Easy Apply for job {job['id']}")
                    await browser.close()
                    return False

                await easy_apply.click()
                await asyncio.sleep(2)

                for _ in range(6):
                    submit_btn = await page.query_selector("button:has-text('Submit application')")
                    if submit_btn:
                        await submit_btn.click()
                        await asyncio.sleep(2)
                        await browser.close()
                        return True
                    next_btn = await page.query_selector(
                        "button:has-text('Next'), button:has-text('Review')"
                    )
                    if next_btn:
                        await next_btn.click()
                        await asyncio.sleep(2)
                    else:
                        break

                await browser.close()
                return False
        except PWTimeout:
            logger.error(f"[linkedin_apply] Timeout: {job['job_url']}")
            return False
        except Exception as e:
            logger.error(f"[linkedin_apply] Error: {e}")
            return False
