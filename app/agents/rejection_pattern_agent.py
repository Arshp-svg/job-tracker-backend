from collections import Counter
from app.models.job import JobApplication, JobStatus


COMMON_SKILLS = [
    "dsa",
    "data structures",
    "algorithms",
    "system design",
    "backend",
    "frontend",
    "sql",
    "database",
    "api",
    "experience"
]

def analyze_rejection_patterns(jobs: list[JobApplication]) -> dict[str, int]:
    rejected_jobs = [
        job for job in jobs
        if job.status == JobStatus.Rejected and job.notes
    ]

    counter = Counter()

    for job in rejected_jobs:
        notes = job.notes.lower()
        for skill in COMMON_SKILLS:
            if skill in notes:
                counter[skill] += 1

    return [
        {"skill": skill, "count": count}
        for skill, count in counter.most_common()
    ]