import asyncio
import random
from abc import ABC, abstractmethod
from loguru import logger

from core.config import config
from core.state_machine import JobStatus


class BaseApplicator(ABC):
    platform: str = ""

    @abstractmethod
    async def apply(self, job: dict) -> bool:
        pass

    async def human_delay(self):
        await asyncio.sleep(random.uniform(config.MIN_ACTION_DELAY, config.MAX_ACTION_DELAY))


async def process_approved_jobs():
    from core.database import get_jobs_by_status, update_job_status
    from applicators.naukri_applicator import NaukriApplicator
    from applicators.linkedin_applicator import LinkedInApplicator
    from applicators.indeed_applicator import IndeedApplicator
    from applicators.internshala_applicator import InternshalaApplicator

    APPLICATORS: dict[str, BaseApplicator] = {
        "naukri": NaukriApplicator(),
        "linkedin": LinkedInApplicator(),
        "indeed": IndeedApplicator(),
        "internshala": InternshalaApplicator(),
    }

    approved = await get_jobs_by_status(JobStatus.APPROVED)
    if not approved:
        return

    logger.info(f"Applying to {len(approved)} approved jobs")
    for job in approved:
        applicator = APPLICATORS.get(job["platform"])
        if not applicator:
            logger.warning(f"No applicator for platform: {job['platform']}")
            continue
        try:
            await update_job_status(job["id"], JobStatus.APPLYING)
            success = await applicator.apply(job)
            if success:
                await update_job_status(job["id"], JobStatus.APPLIED)
                logger.info(f"Applied: {job['title']} @ {job['company']}")
            else:
                new_retry = job["retry_count"] + 1
                if new_retry >= config.MAX_RETRIES:
                    await update_job_status(
                        job["id"], JobStatus.FAILED,
                        retry_count=new_retry, error_log="Max retries exceeded",
                    )
                    await update_job_status(job["id"], "FAILED_PERMANENT")
                else:
                    await update_job_status(
                        job["id"], JobStatus.FAILED, retry_count=new_retry
                    )
        except Exception as e:
            logger.error(f"Apply crashed for job {job['id']}: {e}")
            try:
                await update_job_status(
                    job["id"], JobStatus.FAILED,
                    retry_count=job["retry_count"] + 1, error_log=str(e)[:500],
                )
            except Exception:
                pass
        await asyncio.sleep(random.uniform(2, 5))
