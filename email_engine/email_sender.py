import asyncio
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from loguru import logger

from core.config import config
from core.state_machine import EmailStatus


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    resume_path: Path | None = None,
) -> bool:
    if not config.GMAIL_ADDRESS or not config.GMAIL_APP_PASSWORD:
        logger.error("Gmail credentials not configured")
        return False
    try:
        msg = MIMEMultipart()
        msg["From"] = config.GMAIL_ADDRESS
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        if resume_path and resume_path.exists():
            with open(resume_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{resume_path.name}"',
            )
            msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(config.GMAIL_ADDRESS, config.GMAIL_APP_PASSWORD)
            server.sendmail(config.GMAIL_ADDRESS, to_email, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")
        return False


async def run_cold_email_batch():
    from core.database import (
        get_cold_emails_by_status, update_email_status, company_emailed_recently
    )

    approved = await get_cold_emails_by_status(EmailStatus.APPROVED)
    if not approved:
        return

    sent_count = 0
    for rec in approved:
        if sent_count >= config.COLD_EMAILS_PER_DAY:
            break
        if await company_emailed_recently(rec["company_domain"]):
            logger.debug(f"Skipping {rec['company_name']} — emailed within 30 days")
            continue
        try:
            await update_email_status(rec["id"], EmailStatus.SENDING)
            success = await send_email(
                to_email=rec["hr_email"],
                subject=rec["subject"],
                body=rec["body"],
                resume_path=config.RESUME_BASE_PATH if config.RESUME_BASE_PATH.exists() else None,
            )
            if success:
                await update_email_status(rec["id"], EmailStatus.SENT)
                sent_count += 1
                logger.info(f"Sent cold email to {rec['company_name']} ({rec['hr_email']})")
            else:
                await update_email_status(rec["id"], EmailStatus.SEND_FAILED)
            await asyncio.sleep(random.uniform(180, 300))
        except Exception as e:
            logger.error(f"Cold email batch error for {rec.get('company_name')}: {e}")
            await update_email_status(rec["id"], EmailStatus.SEND_FAILED)

    logger.info(f"Cold email batch done — {sent_count} sent")
