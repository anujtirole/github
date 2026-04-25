import asyncio
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from core.config import config
from applicators.base_applicator import BaseApplicator


class NaukriApplicator(BaseApplicator):
    platform = "naukri"

    async def apply(self, job: dict) -> bool:
        session_path = config.SESSIONS_DIR / "naukri_cookies.json"
        if not session_path.exists():
            logger.error("[naukri_apply] No session file — run setup_sessions.py")
            return False
        if not job.get("job_url"):
            logger.warning(f"[naukri_apply] No URL for job {job['id']}")
            return False
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(storage_state=str(session_path))
                page = await ctx.new_page()
                await page.goto(job["job_url"], timeout=25000)
                await asyncio.sleep(2)

                apply_btn = await page.query_selector(
                    "button#apply-button, button:has-text('Apply'), a:has-text('Apply Now')"
                )
                if not apply_btn:
                    logger.warning(f"[naukri_apply] No apply button at {job['job_url']}")
                    await browser.close()
                    return False

                await apply_btn.click()
                await asyncio.sleep(3)

                submit = await page.query_selector(
                    "button:has-text('Submit'), button:has-text('Apply')"
                )
                if submit:
                    await submit.click()
                    await asyncio.sleep(2)

                await browser.close()
                return True
        except PWTimeout:
            logger.error(f"[naukri_apply] Timeout: {job['job_url']}")
            return False
        except Exception as e:
            logger.error(f"[naukri_apply] Error: {e}")
            return False
