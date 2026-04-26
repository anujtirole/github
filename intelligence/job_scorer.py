import json
import asyncio
from loguru import logger
import anthropic

from core.config import config
from core.state_machine import JobStatus

_SCORING_PROMPT = """You are a career matching expert. Score this job 0-100 for this candidate.

CANDIDATE PROFILE:
{profile_json}

JOB DESCRIPTION:
{job_description}

Score criteria:
- 80-100: Near-perfect match, apply immediately
- 60-79: Good match, worth applying
- 40-59: Partial match, apply if volume is low
- 0-39: Poor match, skip

Return ONLY valid JSON (no markdown, no explanation):
{{"score": <int>, "reason": "<one sentence>", "key_matches": ["skill1"], "gaps": ["gap1"]}}"""


async def score_job(job: dict, profile: dict) -> dict:
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    prompt = _SCORING_PROMPT.format(
        profile_json=json.dumps(profile, indent=2),
        job_description=(
            f"{job.get('title', '')} at {job.get('company', '')}\n\n"
            f"{job.get('description', '')[:3000]}"
        ),
    )
    try:
        response = await client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Score JSON parse error for job {job.get('id')}: {e}")
        return {"score": 0, "reason": "Parse error", "key_matches": [], "gaps": []}
    except anthropic.RateLimitError:
        logger.warning("Claude rate limit hit — backing off 1 hour")
        await asyncio.sleep(3600)
        return {"score": 0, "reason": "Rate limited", "key_matches": [], "gaps": []}
    except Exception as e:
        logger.error(f"Scoring API error for job {job.get('id')}: {e}")
        return {"score": 0, "reason": str(e)[:200], "key_matches": [], "gaps": []}


async def score_pending_jobs():
    from core.database import get_jobs_by_status, update_job_status, update_job_score

    if not config.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — skipping scoring")
        return

    profile: dict = {}
    if config.PROFILE_PATH.exists():
        profile = json.loads(config.PROFILE_PATH.read_text())

    discovered = await get_jobs_by_status(JobStatus.DISCOVERED)
    if not discovered:
        return

    logger.info(f"Scoring {len(discovered)} jobs")
    for job in discovered:
        try:
            await update_job_status(job["id"], JobStatus.SCORING)
            result = await score_job(job, profile)
            score = int(result.get("score", 0))
            reason = result.get("reason", "")
            if score < config.AUTO_REJECT_BELOW:
                await update_job_status(job["id"], JobStatus.REJECTED)
                logger.debug(f"Auto-rejected (score={score}): {job['title']} @ {job['company']}")
            else:
                await update_job_score(job["id"], score, reason)
                logger.info(f"Score {score}/100: {job['title']} @ {job['company']} — {reason}")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Score failed for job {job['id']}: {e}")
