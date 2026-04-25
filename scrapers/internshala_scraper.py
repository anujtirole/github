import httpx
from bs4 import BeautifulSoup
from loguru import logger

from core.config import config
from scrapers.base_scraper import BaseScraper

INTERNSHALA_BASE = "https://internshala.com"
_CATEGORIES = [
    "machine-learning-jobs",
    "artificial-intelligence-jobs",
    "data-science-jobs",
    "software-development-jobs",
]
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


class InternshalaSccraper(BaseScraper):
    platform = "internshala"

    async def login(self) -> bool:
        return True

    async def is_session_valid(self) -> bool:
        return True

    async def search_jobs(self) -> list[dict]:
        all_jobs: list[dict] = []
        async with httpx.AsyncClient(headers=_HEADERS, timeout=30, follow_redirects=True) as client:
            for cat in _CATEGORIES:
                try:
                    resp = await client.get(f"{INTERNSHALA_BASE}/jobs/{cat}/")
                    soup = BeautifulSoup(resp.text, "lxml")
                    for card in soup.select("div.individual_internship"):
                        try:
                            link = card.select_one("a.job-title-href")
                            company_el = card.select_one("p.company-name")
                            loc_el = card.select_one("div.location_link")
                            if not (link and company_el):
                                continue
                            href = link.get("href", "")
                            job_id = href.rstrip("/").split("/")[-1]
                            all_jobs.append({
                                "jobId": job_id,
                                "title": link.get_text(strip=True),
                                "company": company_el.get_text(strip=True),
                                "location": loc_el.get_text(strip=True) if loc_el else "",
                                "url": f"{INTERNSHALA_BASE}{href}" if href else "",
                                "description": "",
                            })
                        except Exception:
                            continue
                    await self.human_delay()
                except Exception as e:
                    logger.error(f"[internshala] Category '{cat}' failed: {e}")
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
