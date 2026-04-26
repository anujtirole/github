import json
from pathlib import Path
from loguru import logger
import anthropic

from core.config import config

_TAILOR_PROMPT = """You are a resume optimization expert. Given this candidate's resume and a job description,
rewrite the professional summary and reorder bullets to best match the job.

BASE RESUME:
{resume_text}

JOB:
Title: {job_title}
Company: {job_company}
Description: {job_description}

Instructions:
1. Rewrite the professional summary (2-3 sentences) mirroring job keywords
2. Reorder experience bullets to front-load most relevant achievements
3. Never fabricate anything — only reorder and rewrite
4. Output clean plain text resume, ready for PDF conversion

Return only the resume text."""


async def tailor_resume(job: dict) -> Path | None:
    if not config.ANTHROPIC_API_KEY:
        return None
    if not config.RESUME_BASE_PATH.exists():
        logger.warning(f"Base resume not found at {config.RESUME_BASE_PATH}")
        return None

    resume_text = config.RESUME_BASE_PATH.read_bytes().decode("utf-8", errors="ignore")
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        response = await client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": _TAILOR_PROMPT.format(
                resume_text=resume_text[:4000],
                job_title=job.get("title", ""),
                job_company=job.get("company", ""),
                job_description=job.get("description", "")[:2000],
            )}],
        )
        output_dir = config.RESUME_TAILORED_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{job['id']}.txt"
        out_path.write_text(response.content[0].text)
        logger.info(f"Tailored resume saved: {out_path}")
        return out_path
    except Exception as e:
        logger.error(f"Resume tailoring failed for job {job['id']}: {e}")
        return None
