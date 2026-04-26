import httpx
from loguru import logger

from core.config import config
from scrapers.base_scraper import BaseScraper

NAUKRI_SEARCH_URL = "https://www.naukri.com/jobapi/v3/search"
NAUKRI_HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "appid": "109",
    "clientid": "d3skt0p",
    "content-type": "application/json",
    "systemid": "Naukri",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
}


class NaukriScraper(BaseScraper):
    platform = "naukri"

    async def login(self) -> bool:
        logger.info("[naukri] Run setup_sessions.py to save login cookies")
        return self.session_path.exists()

    async def is_session_valid(self) -> bool:
        return self.session_path.exists()

    async def search_jobs(self) -> list[dict]:
        all_jobs: list[dict] = []
        async with httpx.AsyncClient(headers=NAUKRI_HEADERS, timeout=30) as client:
            for keyword in config.SEARCH_KEYWORDS[:6]:
                try:
                    resp = await client.get(
                        NAUKRI_SEARCH_URL,
                        params={
                            "noOfResults": 20,
                            "urlType": "search_by_keyword",
                            "searchType": "adv",
                            "keyword": keyword,
                            "location": "india",
                            "experience": 0,
                            "sort": 1,
                            "pageNo": 1,
                        },
                    )
                    resp.raise_for_status()
                    all_jobs.extend(resp.json().get("jobDetails", []) or [])
                    await self.human_delay()
                except Exception as e:
                    logger.error(f"[naukri] Keyword '{keyword}' failed: {e}")
        return all_jobs

    async def parse_job(self, raw: dict) -> dict | None:
        try:
            title = raw.get("title", "").strip()
            company = raw.get("companyName", "").strip()
            if not title or not company:
                return None
            placeholders = raw.get("placeholders") or []
            location = placeholders[0].get("label", "") if placeholders else ""
            return {
                "platform": self.platform,
                "platform_job_id": str(raw.get("jobId", "")),
                "title": title,
                "company": company,
                "location": location,
                "salary_min": None,
                "salary_max": None,
                "job_url": raw.get("jdURL", ""),
                "description": raw.get("jobDescription", ""),
            }
        except Exception as e:
            logger.debug(f"[naukri] parse_job error: {e}")
            return None
