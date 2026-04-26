import httpx
from loguru import logger

from core.config import config


async def find_emails(domain: str) -> list[dict]:
    emails: list[dict] = []
    if config.HUNTER_IO_API_KEY:
        emails = await _hunter_search(domain)
    if not emails and config.APOLLO_API_KEY:
        emails = await _apollo_search(domain)
    return emails


async def _hunter_search(domain: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": config.HUNTER_IO_API_KEY, "limit": 5},
            )
            resp.raise_for_status()
            emails_raw = resp.json().get("data", {}).get("emails", [])
            return [
                {"email": e["value"], "type": e.get("type", "generic"), "source": "hunter"}
                for e in emails_raw
            ]
    except Exception as e:
        logger.error(f"Hunter.io search failed for {domain}: {e}")
        return []


async def _apollo_search(domain: str) -> list[dict]:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.apollo.io/v1/mixed_people/search",
                headers={"Content-Type": "application/json"},
                json={
                    "api_key": config.APOLLO_API_KEY,
                    "q_organization_domains": domain,
                    "page": 1, "per_page": 3,
                    "person_titles": ["HR", "Recruiter", "Talent Acquisition", "Hiring"],
                },
            )
            people = resp.json().get("people", [])
            return [
                {"email": p["email"], "type": "hr", "source": "apollo"}
                for p in people if p.get("email")
            ]
    except Exception as e:
        logger.error(f"Apollo search failed for {domain}: {e}")
        return []
