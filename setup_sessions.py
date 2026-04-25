"""Run this once to save login cookies for each platform.
A visible browser opens so you can log in manually.
Cookies are saved to data/sessions/ and reused by the scraper."""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright
from core.config import config


PLATFORMS = {
    "naukri": {
        "url": "https://www.naukri.com/nlogin/login",
        "wait_selector": "a[title='View & Update Profile']",
        "cookie_file": "naukri_cookies.json",
    },
    "linkedin": {
        "url": "https://www.linkedin.com/login",
        "wait_selector": "div.global-nav",
        "cookie_file": "linkedin_cookies.json",
    },
    "indeed": {
        "url": "https://secure.indeed.com/account/login",
        "wait_selector": "a[data-gnav-element-name='SignIn']",
        "cookie_file": "indeed_cookies.json",
    },
    "internshala": {
        "url": "https://internshala.com/login/user",
        "wait_selector": "a.logout-link",
        "cookie_file": "internshala_cookies.json",
    },
}


async def save_session(platform: str, info: dict):
    session_path = config.SESSIONS_DIR / info["cookie_file"]
    print(f"\n[{platform}] Opening browser — please log in, then press ENTER here.")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        await page.goto(info["url"])
        input(f"  >> Log in to {platform} in the browser, then press ENTER to save session...")
        storage = await ctx.storage_state()
        session_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        session_path.write_text(json.dumps(storage, indent=2))
        await browser.close()
        print(f"  [OK] Session saved to {session_path}")


async def main():
    target = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    platforms = (
        {target: PLATFORMS[target]}
        if target in PLATFORMS
        else PLATFORMS
    )
    for name, info in platforms.items():
        await save_session(name, info)
    print("\nAll sessions saved. Run: python main.py")


if __name__ == "__main__":
    asyncio.run(main())
