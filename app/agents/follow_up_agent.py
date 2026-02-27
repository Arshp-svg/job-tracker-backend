from datetime import datetime, timedelta
from app.models.job import JobApplication, JobStatus

FOLLOW_UP_DAYS = 15  # Number of days after which to follow up

def evaluate_follow_up(job: JobApplication) -> bool:
    # accept either enum status or string status from model/fixtures
    status = getattr(job, "status", None)
    if isinstance(status, str):
        if status.lower() != "applied":
            return False
    else:
        if status != JobStatus.Applied:
            return False

    applied_date = getattr(job, "applied_date", None)
    if not applied_date:
        return False

    days_since_application = (datetime.now() - applied_date).days
    return days_since_application >= FOLLOW_UP_DAYS

def generate_follow_up_email(company: str, role: str) -> str:
    return (
        f"Hi Hiring Team,\n\n"
        f"I hope you're doing well. I wanted to follow up on my application "
        f"for the {role} position at {company}. "
        f"I’m very interested in the opportunity and would love to hear "
        f"about any next steps.\n\n"
        f"Thank you for your time and consideration.\n\n"
        f"Best regards,\n"
        f"[Your Name]"
    )
