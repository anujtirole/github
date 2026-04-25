import asyncio
from loguru import logger
from playwright.async_api import async_playwright

from core.config import config
from scrapers.base_scraper import BaseScraper


class LinkedInScraper(BaseScraper):
    platform = "linkedin"

    async def login(self) -> bool:
        logger.info("[linkedin] Run setup_sessions.py to save login cookies")
        return self.session_path.exists()

    async def is_session_valid(self) -> bool:
        if not self.session_path.exists():
            return False
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(storage_state=str(self.session_path))
                page = await ctx.new_page()
                await page.goto("https://www.linkedin.com/feed/", timeout=15000)
                valid = "feed" in page.url or "mynetwork" in page.url
                await browser.close()
                return valid
        except Exception as e:
            logger.warning(f"[linkedin] Session check failed: {e}")
            return False

    async def search_jobs(self) -> list[dict]:
        all_jobs: list[dict] = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            ctx = await browser.new_context(storage_state=str(self.session_path))
            page = await ctx.new_page()
            for keyword in config.SEARCH_KEYWORDS[:4]:
                try:
                    url = (
                        f"https://www.linkedin.com/jobs/search/"
                        f"?keywords={keyword.replace(' ', '+')}"
                        f"&location=India&f_TPR=r86400&f_EA=true"
                    )
                    await page.goto(url, timeout=20000)
                    await asyncio.sleep(3)
                    for _ in range(3):
                        await page.keyboard.press("End")
                        await asyncio.sleep(1.5)
                    cards = await page.query_selector_all(".job-search-card")
                    for card in cards[:20]:
                        try:
                            job_id = await card.get_attribute("data-job-id") or ""
                            title_el = await card.query_selector(".base-search-card__title")
                            company_el = await card.query_selector(".base-search-card__subtitle")
                            location_el = await card.query_selector(".job-search-card__location")
                            link_el = await card.query_selector("a.base-card__full-link")
                            title = (await title_el.inner_text()).strip() if title_el else ""
                            company = (await company_el.inner_text()).strip() if company_el else ""
                            location = (await location_el.inner_text()).strip() if location_el else ""
                            job_url = await link_el.get_attribute("href") if link_el else ""
                            if title and company:
                                all_jobs.append({
                                    "jobId": job_id, "title": title, "company": company,
                                    "location": location, "url": job_url,
                                })
                        except Exception:
                            continue
                    await self.human_delay()
                except Exception as e:
                    logger.error(f"[linkedin] Keyword '{keyword}' failed: {e}")
            await browser.close()
        return all_jobs

    async def parse_job(self, raw: dict) -> dict | None:
        if not raw.get("title") or not raw.get("company"):
            return None
        return {
            "platform": self.platform,
            "platform_job_id": str(raw.get("jobId", "")),
            "title": raw["title"],
            "company": raw["company"],
            "location": raw.get("location", ""),
            "salary_min": None,
            "salary_max": None,
            "job_url": raw.get("url", ""),
            "description": raw.get("description", ""),
        }
