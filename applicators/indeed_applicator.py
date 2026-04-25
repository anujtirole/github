import asyncio
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from core.config import config
from applicators.base_applicator import BaseApplicator


class IndeedApplicator(BaseApplicator):
    platform = "indeed"

    async def apply(self, job: dict) -> bool:
        if not job.get("job_url"):
            return False
        session_path = config.SESSIONS_DIR / "indeed_cookies.json"
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx_kwargs = {}
                if session_path.exists():
                    ctx_kwargs["storage_state"] = str(session_path)
                ctx = await browser.new_context(**ctx_kwargs)
                page = await ctx.new_page()
                await page.goto(job["job_url"], timeout=25000)
                await asyncio.sleep(2)

                apply_btn = await page.query_selector(
                    "button#indeedApplyButton, a:has-text('Apply now'), button:has-text('Apply now')"
                )
                if not apply_btn:
                    await browser.close()
                    return False

                await apply_btn.click()
                await asyncio.sleep(3)

                for step_sel in [
                    "button:has-text('Continue')",
                    "button:has-text('Submit your application')",
                    "button:has-text('Submit')",
                ]:
                    btn = await page.query_selector(step_sel)
                    if btn:
                        await btn.click()
                        await asyncio.sleep(2)

                await browser.close()
                return True
        except PWTimeout:
            logger.error(f"[indeed_apply] Timeout: {job['job_url']}")
            return False
        except Exception as e:
            logger.error(f"[indeed_apply] Error: {e}")
            return False
