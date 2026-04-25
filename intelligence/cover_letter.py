import json
from loguru import logger
import anthropic

from core.config import config

_COVER_LETTER_PROMPT = """Write a sharp, 3-paragraph cover letter for this role.
Paragraph 1: Why this company excites me (specific, researched)
Paragraph 2: My 2 most relevant achievements (numbers where possible)
Paragraph 3: Clear ask + availability

Tone: Confident, direct, not sycophantic. No \"I am writing to express my interest.\"

Candidate: {profile}
Job: {job_description}
Company: {company_name}

Return only the cover letter text, no subject line."""


async def generate_cover_letter(job: dict) -> str:
    if not config.ANTHROPIC_API_KEY:
        return ""
    profile: dict = {}
    if config.PROFILE_PATH.exists():
        profile = json.loads(config.PROFILE_PATH.read_text())
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        response = await client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": _COVER_LETTER_PROMPT.format(
                profile=json.dumps(profile, indent=2),
                job_description=(
                    f"{job.get('title', '')} at {job.get('company', '')}\n"
                    f"{job.get('description', '')[:2000]}"
                ),
                company_name=job.get("company", ""),
            )}],
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        return ""
