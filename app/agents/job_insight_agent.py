from app.models.job import JobApplication, JobStatus
from app.llm.llm_client import call_llm

def generate_job_insight(job: JobApplication, previous_rejections: int) -> str:
    base_insight = ""

    if job.status == JobStatus.Rejected:
        base_insight = (
            f"The candidate was rejected for the {job.role} role at {job.company}. "
            "Suggest improvements and future strategy."
        )
    elif previous_rejections > 0:
        base_insight = (
            f"The candidate previously faced {previous_rejections} rejections for "
            f"{job.role} at {job.company}. Recommend next steps."
        )
    else:
        base_insight = (
            f"The candidate applied for {job.role} at {job.company}. "
            "Suggest follow-up strategy."
        )

    return call_llm(base_insight)
