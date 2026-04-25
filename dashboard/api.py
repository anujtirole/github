from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from core.database import (
    get_jobs_by_status, update_job_status, get_stats,
    get_cold_emails_by_status, update_email_status,
)
from core.state_machine import JobStatus, EmailStatus

app = FastAPI(title="JobHunterX", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"


class DecisionRequest(BaseModel):
    decision: str  # "yes" or "no"


@app.get("/api/pending")
async def get_pending_jobs():
    return await get_jobs_by_status(JobStatus.PENDING_APPROVAL)


@app.get("/api/emails/pending")
async def get_pending_emails():
    return await get_cold_emails_by_status(EmailStatus.PENDING_APPROVAL)


@app.post("/api/decision/{job_id}")
async def make_job_decision(job_id: int, req: DecisionRequest):
    if req.decision not in ("yes", "no"):
        raise HTTPException(400, "decision must be 'yes' or 'no'")
    new_status = JobStatus.APPROVED if req.decision == "yes" else JobStatus.REJECTED
    try:
        await update_job_status(job_id, new_status)
        return {"status": "ok", "job_id": job_id, "new_status": new_status}
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/email-decision/{email_id}")
async def make_email_decision(email_id: int, req: DecisionRequest):
    if req.decision not in ("yes", "no"):
        raise HTTPException(400, "decision must be 'yes' or 'no'")
    new_status = EmailStatus.APPROVED if req.decision == "yes" else EmailStatus.REJECTED
    try:
        await update_email_status(email_id, new_status)
        return {"status": "ok", "email_id": email_id, "new_status": new_status}
    except Exception as e:
        raise HTTPException(400, str(e))


@app.get("/api/stats")
async def get_dashboard_stats():
    return await get_stats()


@app.get("/api/history")
async def get_applied_history():
    return await get_jobs_by_status(JobStatus.APPLIED)


@app.get("/api/failed")
async def get_failed_jobs():
    return await get_jobs_by_status(JobStatus.FAILED)


@app.get("/api/needs-manual")
async def get_manual_jobs():
    return await get_jobs_by_status(JobStatus.NEEDS_MANUAL)


if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
else:
    @app.get("/")
    async def root():
        return {
            "message": "JobHunterX API is running.",
            "hint": "Build the frontend: cd dashboard/frontend && npm install && npm run build",
        }
