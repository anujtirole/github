import httpx
from bs4 import BeautifulSoup
from loguru import logger

from core.config import config
from scrapers.base_scraper import BaseScraper

INDEED_BASE = "https://in.indeed.com"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


class IndeedScraper(BaseScraper):
    platform = "indeed"

    async def login(self) -> bool:
        return True

    async def is_session_valid(self) -> bool:
        return True

    async def search_jobs(self) -> list[dict]:
        all_jobs: list[dict] = []
        async with httpx.AsyncClient(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
            for keyword in config.SEARCH_KEYWORDS[:4]:
                try:
                    resp = await client.get(
                        f"{INDEED_BASE}/jobs",
                        params={"q": keyword, "l": "India", "sort": "date", "fromage": "1"},
                    )
                    soup = BeautifulSoup(resp.text, "lxml")
                    for card in soup.select("div.job_seen_beacon"):
                        try:
                            job_id = card.get("data-jk", "")
                            title_el = card.select_one("h2.jobTitle span")
                            company_el = card.select_one("span.companyName")
                            location_el = card.select_one("div.companyLocation")
                            snippet_el = card.select_one("div.job-snippet")
                            if title_el and company_el:
                                all_jobs.append({
                                    "jobId": job_id,
                                    "title": title_el.get_text(strip=True),
                                    "company": company_el.get_text(strip=True),
                                    "location": location_el.get_text(strip=True) if location_el else "",
                                    "url": f"{INDEED_BASE}/viewjob?jk={job_id}" if job_id else "",
                                    "description": snippet_el.get_text(strip=True) if snippet_el else "",
                                })
                        except Exception:
                            continue
                    await self.human_delay()
                except Exception as e:
                    logger.error(f"[indeed] Keyword '{keyword}' failed: {e}")
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
