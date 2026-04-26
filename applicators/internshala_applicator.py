import asyncio
from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

from core.config import config
from applicators.base_applicator import BaseApplicator


class InternshalaApplicator(BaseApplicator):
    platform = "internshala"

    async def apply(self, job: dict) -> bool:
        session_path = config.SESSIONS_DIR / "internshala_cookies.json"
        if not session_path.exists():
            logger.error("[internshala_apply] No session — run setup_sessions.py")
            return False
        if not job.get("job_url"):
            return False
        try:
            from intelligence.cover_letter import generate_cover_letter
            cover = await generate_cover_letter(job)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(storage_state=str(session_path))
                page = await ctx.new_page()
                await page.goto(job["job_url"], timeout=25000)
                await asyncio.sleep(2)

                apply_btn = await page.query_selector(
                    "a#apply_now_btn, button:has-text('Apply'), a:has-text('Apply Now')"
                )
                if not apply_btn:
                    await browser.close()
                    return False

                await apply_btn.click()
                await asyncio.sleep(2)

                cover_field = await page.query_selector("textarea#cover_letter")
                if cover_field and cover:
                    await cover_field.fill(cover)
                    await asyncio.sleep(1)

                submit = await page.query_selector(
                    "button#submit, button:has-text('Submit'), input[type='submit']"
                )
                if submit:
                    await submit.click()
                    await asyncio.sleep(2)
                    await browser.close()
                    return True

                await browser.close()
                return False
        except PWTimeout:
            logger.error(f"[internshala_apply] Timeout: {job['job_url']}")
            return False
        except Exception as e:
            logger.error(f"[internshala_apply] Error: {e}")
            return False
