class JobStatus:
    DISCOVERED = "DISCOVERED"
    SCORING = "SCORING"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    APPLYING = "APPLYING"
    APPLIED = "APPLIED"
    FAILED = "FAILED"
    FAILED_PERMANENT = "FAILED_PERMANENT"
    NEEDS_MANUAL = "NEEDS_MANUAL"
    SKIPPED = "SKIPPED"


class EmailStatus:
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    SENDING = "SENDING"
    SENT = "SENT"
    SEND_FAILED = "SEND_FAILED"
    REPLIED = "REPLIED"


JOB_STATUS = JobStatus
EMAIL_STATUS = EmailStatus

VALID_JOB_TRANSITIONS: dict[str, set] = {
    JobStatus.DISCOVERED: {JobStatus.SCORING, JobStatus.SKIPPED},
    JobStatus.SCORING: {JobStatus.PENDING_APPROVAL, JobStatus.REJECTED, JobStatus.SKIPPED},
    JobStatus.PENDING_APPROVAL: {JobStatus.APPROVED, JobStatus.REJECTED},
    JobStatus.APPROVED: {JobStatus.APPLYING, JobStatus.REJECTED},
    JobStatus.APPLYING: {JobStatus.APPLIED, JobStatus.FAILED, JobStatus.NEEDS_MANUAL},
    JobStatus.FAILED: {JobStatus.APPLYING, JobStatus.FAILED_PERMANENT},
    JobStatus.APPLIED: set(),
    JobStatus.REJECTED: set(),
    JobStatus.FAILED_PERMANENT: set(),
    JobStatus.NEEDS_MANUAL: {JobStatus.APPROVED, JobStatus.REJECTED},
    JobStatus.SKIPPED: set(),
}

VALID_EMAIL_TRANSITIONS: dict[str, set] = {
    EmailStatus.DRAFT: {EmailStatus.PENDING_APPROVAL},
    EmailStatus.PENDING_APPROVAL: {EmailStatus.APPROVED, EmailStatus.REJECTED},
    EmailStatus.APPROVED: {EmailStatus.SENDING},
    EmailStatus.SENDING: {EmailStatus.SENT, EmailStatus.SEND_FAILED},
    EmailStatus.SENT: {EmailStatus.REPLIED},
    EmailStatus.SEND_FAILED: {EmailStatus.SENDING},
    EmailStatus.REJECTED: set(),
    EmailStatus.REPLIED: set(),
}


def validate_transition(current: str, target: str) -> None:
    allowed = VALID_JOB_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid job state transition: {current} -> {target}. Allowed: {allowed}"
        )


def validate_email_transition(current: str, target: str) -> None:
    allowed = VALID_EMAIL_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ValueError(
            f"Invalid email state transition: {current} -> {target}. Allowed: {allowed}"
        )
