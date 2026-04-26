import json
from loguru import logger
import anthropic

from core.config import config

_COLD_EMAIL_PROMPT = """Write a cold email to the HR/recruiter at {company_name} for a {target_role} position.

Rules:
- Subject line: Under 8 words, specific, no clickbait
- Body: 4-5 sentences max
- Open with something specific about {company_name}'s AI work
- Mention ONE quantified achievement
- Clear ask: 15-minute call or to forward to hiring manager
- Sign off with name, LinkedIn URL, GitHub URL

Candidate: {profile}
Company context: {company_context}

Return JSON only:
{{"subject": "...", "body": "..."}}"""


async def compose_cold_email(company: dict, profile: dict) -> dict:
    if not config.ANTHROPIC_API_KEY:
        return {}
    client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    try:
        response = await client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": _COLD_EMAIL_PROMPT.format(
                company_name=company.get("name", ""),
                target_role="Gen AI / LLM Engineer",
                profile=json.dumps(profile, indent=2),
                company_context=company.get(
                    "context",
                    f"{company.get('name')} is a leading technology company.",
                ),
            )}],
        )
        return json.loads(response.content[0].text.strip())
    except json.JSONDecodeError as e:
        logger.error(f"Cold email JSON parse error for {company.get('name')}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Cold email composition failed for {company.get('name')}: {e}")
        return {}
