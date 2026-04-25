import asyncio
import random
from abc import ABC, abstractmethod
from loguru import logger

from core.config import config


class BaseScraper(ABC):
    platform: str = ""

    def __init__(self):
        self.session_path = config.SESSIONS_DIR / f"{self.platform}_cookies.json"
        config.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def login(self) -> bool:
        pass

    @abstractmethod
    async def search_jobs(self) -> list[dict]:
        pass

    @abstractmethod
    async def parse_job(self, raw: dict) -> dict | None:
        pass

    @abstractmethod
    async def is_session_valid(self) -> bool:
        pass

    async def run(self) -> list[dict]:
        logger.info(f"[{self.platform}] Starting scrape")
        if not await self.is_session_valid():
            logger.warning(f"[{self.platform}] Session invalid, attempting login")
            if not await self.login():
                logger.error(f"[{self.platform}] Login failed, skipping")
                return []
        try:
            raw_jobs = await self.search_jobs()
            jobs = []
            for raw in raw_jobs:
                parsed = await self.parse_job(raw)
                if parsed:
                    jobs.append(parsed)
            logger.info(f"[{self.platform}] Parsed {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"[{self.platform}] Scrape error: {e}")
            return []

    async def human_delay(self):
        await asyncio.sleep(random.uniform(config.MIN_ACTION_DELAY, config.MAX_ACTION_DELAY))
