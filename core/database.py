import hashlib
import aiosqlite
from datetime import datetime
from loguru import logger

from core.config import config
from core.state_machine import validate_transition, JobStatus, EmailStatus

DB_PATH = config.DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    platform_job_id TEXT NOT NULL,
    dedup_hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    job_url TEXT,
    description TEXT,
    relevance_score INTEGER DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'DISCOVERED',
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    scored_at DATETIME,
    decision_at DATETIME,
    applied_at DATETIME,
    application_ref TEXT,
    retry_count INTEGER DEFAULT 0,
    error_log TEXT,
    UNIQUE(platform, platform_job_id),
    CHECK(status IN (
        'DISCOVERED','SCORING','PENDING_APPROVAL','APPROVED','REJECTED',
        'APPLYING','APPLIED','FAILED','FAILED_PERMANENT','NEEDS_MANUAL','SKIPPED'
    ))
);

CREATE TABLE IF NOT EXISTS cold_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    company_domain TEXT NOT NULL,
    hr_email TEXT NOT NULL,
    email_type TEXT,
    subject TEXT,
    body TEXT,
    resume_version TEXT,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    decision_at DATETIME,
    sent_at DATETIME,
    reply_received BOOLEAN DEFAULT 0,
    reply_at DATETIME,
    UNIQUE(company_domain, hr_email),
    CHECK(status IN ('DRAFT','PENDING_APPROVAL','APPROVED','REJECTED','SENDING','SENT','SEND_FAILED','REPLIED'))
);

CREATE TABLE IF NOT EXISTS system_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    module TEXT NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_dedup ON jobs(dedup_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform, platform_job_id);
CREATE INDEX IF NOT EXISTS idx_emails_status ON cold_emails(status);
CREATE INDEX IF NOT EXISTS idx_emails_domain ON cold_emails(company_domain);
"""


async def init_db():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    logger.info(f"Database initialized at {DB_PATH}")


def make_dedup_hash(company: str, title: str, location: str) -> str:
    raw = f"{company.lower().strip()}|{title.lower().strip()}|{location.lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def job_exists(dedup_hash: str, platform: str, platform_job_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM jobs WHERE dedup_hash=? OR (platform=? AND platform_job_id=?)",
            (dedup_hash, platform, platform_job_id),
        )
        return (await cursor.fetchone()) is not None


async def insert_job(job: dict) -> int | None:
    dedup_hash = make_dedup_hash(
        job["company"], job["title"], job.get("location", "")
    )
    if await job_exists(dedup_hash, job["platform"], job["platform_job_id"]):
        logger.debug(f"Duplicate skipped: {job['title']} @ {job['company']}")
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO jobs (platform, platform_job_id, dedup_hash, title, company,
                location, salary_min, salary_max, job_url, description, status)
            VALUES (?,?,?,?,?,?,?,?,?,?,'DISCOVERED')
            """,
            (
                job["platform"], job["platform_job_id"], dedup_hash,
                job["title"], job["company"], job.get("location", ""),
                job.get("salary_min"), job.get("salary_max"),
                job.get("job_url", ""), job.get("description", ""),
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_jobs_by_status(status: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM jobs WHERE status=? ORDER BY relevance_score DESC, discovered_at DESC",
            (status,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]


async def update_job_status(job_id: int, new_status: str, **kwargs):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT status FROM jobs WHERE id=?", (job_id,))
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Job {job_id} not found")
        validate_transition(row[0], new_status)

        timestamp_cols = {
            "PENDING_APPROVAL": "scored_at",
            "APPROVED": "decision_at",
            "REJECTED": "decision_at",
            "APPLIED": "applied_at",
        }
        set_parts = ["status=?"]
        params: list = [new_status]
        if new_status in timestamp_cols:
            set_parts.append(f"{timestamp_cols[new_status]}=CURRENT_TIMESTAMP")
        for k, v in kwargs.items():
            set_parts.append(f"{k}=?")
            params.append(v)
        params.append(job_id)
        await db.execute(
            f"UPDATE jobs SET {', '.join(set_parts)} WHERE id=?", params
        )
        await db.commit()


async def update_job_score(job_id: int, score: int, reason: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE jobs SET relevance_score=?, error_log=?, status='PENDING_APPROVAL', "
            "scored_at=CURRENT_TIMESTAMP WHERE id=?",
            (score, reason, job_id),
        )
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        today = datetime.now().strftime("%Y-%m-%d")

        async def count(sql, params=()):
            cur = await db.execute(sql, params)
            row = await cur.fetchone()
            return row[0] if row else 0

        return {
            "applied_today": await count(
                "SELECT COUNT(*) FROM jobs WHERE status='APPLIED' AND DATE(applied_at)=?", (today,)
            ),
            "applied_total": await count("SELECT COUNT(*) FROM jobs WHERE status='APPLIED'"),
            "pending_approval": await count("SELECT COUNT(*) FROM jobs WHERE status='PENDING_APPROVAL'"),
            "emails_today": await count(
                "SELECT COUNT(*) FROM cold_emails WHERE status='SENT' AND DATE(sent_at)=?", (today,)
            ),
            "email_replies": await count("SELECT COUNT(*) FROM cold_emails WHERE reply_received=1"),
            "failed_jobs": await count("SELECT COUNT(*) FROM jobs WHERE status='FAILED'"),
        }


async def log_system_event(module: str, level: str, message: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO system_log (module, level, message) VALUES (?,?,?)",
            (module, level, message),
        )
        await db.commit()


async def get_cold_emails_by_status(status: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM cold_emails WHERE status=? ORDER BY discovered_at DESC", (status,)
        )
        return [dict(r) for r in await cursor.fetchall()]


async def insert_cold_email(email: dict) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            cursor = await db.execute(
                """
                INSERT INTO cold_emails
                    (company_name, company_domain, hr_email, email_type, subject, body, resume_version, status)
                VALUES (?,?,?,?,?,?,?,'DRAFT')
                """,
                (
                    email["company_name"], email["company_domain"], email["hr_email"],
                    email.get("email_type", "hr"), email.get("subject", ""),
                    email.get("body", ""), email.get("resume_version", "base"),
                ),
            )
            await db.commit()
            return cursor.lastrowid
        except aiosqlite.IntegrityError:
            logger.debug(f"Duplicate email skipped: {email['company_domain']} / {email['hr_email']}")
            return None


async def update_email_status(email_id: int, new_status: str, **kwargs):
    from core.state_machine import validate_email_transition
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT status FROM cold_emails WHERE id=?", (email_id,))
        row = await cursor.fetchone()
        if not row:
            raise ValueError(f"Email {email_id} not found")
        validate_email_transition(row[0], new_status)
        set_parts = ["status=?"]
        params: list = [new_status]
        if new_status == "APPROVED":
            set_parts.append("decision_at=CURRENT_TIMESTAMP")
        elif new_status == "SENT":
            set_parts.append("sent_at=CURRENT_TIMESTAMP")
        for k, v in kwargs.items():
            set_parts.append(f"{k}=?")
            params.append(v)
        params.append(email_id)
        await db.execute(f"UPDATE cold_emails SET {', '.join(set_parts)} WHERE id=?", params)
        await db.commit()


async def company_emailed_recently(domain: str, days: int = 30) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id FROM cold_emails WHERE company_domain=? AND status IN ('SENT','SEND_FAILED') "
            "AND sent_at > datetime('now', ?)",
            (domain, f"-{days} days"),
        )
        return (await cursor.fetchone()) is not None


async def reset_stuck_applying_jobs():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE jobs SET status='APPROVED' WHERE status='APPLYING'")
        await db.execute(
            "UPDATE jobs SET status='APPROVED' WHERE status='FAILED' AND retry_count < ?",
            (config.MAX_RETRIES,),
        )
        await db.commit()
    logger.info("Crash recovery: stuck APPLYING jobs reset to APPROVED")
