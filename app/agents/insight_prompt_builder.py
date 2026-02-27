from collections import Counter
from app.models.job import JobApplication, JobStatus

def build_insight_prompt(jobs: list[JobApplication]) -> str:
    if not jobs:
        return "The user has not added any job applications yet."

    total = len(jobs)
    status_counts = Counter(job.status for job in jobs)
    company_counts = Counter(job.company for job in jobs)

    rejected_companies = [
        company for company, count in company_counts.items()
        if count > 1
    ]

    prompt = f"""
You are an AI career assistant.

Here is the user's job application data:

Total applications: {total}
Status breakdown:
- Applied: {status_counts.get(JobStatus.Applied, 0)}
- Interview: {status_counts.get(JobStatus.Interview, 0)}
- Rejected: {status_counts.get(JobStatus.Rejected, 0)}
- Offer: {status_counts.get(JobStatus.Offer, 0)}

Companies applied to more than once:
{', '.join(rejected_companies) if rejected_companies else 'None'}

Your task:
1. Identify patterns in rejections or progress
2. Suggest improvements in job strategy
3. Recommend next actions

Respond in clear, friendly natural language.
"""
    return prompt.strip()
