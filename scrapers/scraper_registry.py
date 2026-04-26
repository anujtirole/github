from loguru import logger

from core.database import insert_job
from scrapers.naukri_scraper import NaukriScraper
from scrapers.linkedin_scraper import LinkedInScraper
from scrapers.indeed_scraper import IndeedScraper
from scrapers.internshala_scraper import InternshalaSccraper

SCRAPERS = [NaukriScraper, LinkedInScraper, IndeedScraper, InternshalaSccraper]


async def run_all_scrapers() -> int:
    logger.info("=== Scrape cycle START ===")
    total_new = 0
    for ScraperClass in SCRAPERS:
        scraper = ScraperClass()
        try:
            jobs = await scraper.run()
            for job in jobs:
                job_id = await insert_job(job)
                if job_id:
                    total_new += 1
        except Exception as e:
            logger.error(f"{ScraperClass.__name__} crashed: {e}")
    logger.info(f"=== Scrape cycle END — {total_new} new jobs ===")
    return total_new
