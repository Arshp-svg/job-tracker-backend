from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import SessionLocal
from app.models.job import JobApplication, JobStatus
from app.models.user import User
from app.agents.llm_agent import generate_insight_summary
from app.agents.rejection_pattern_agent import analyze_rejection_patterns
from app.agents.insight_prompt_builder import build_insight_prompt
from app.agents.job_insight_agent import generate_job_insight
from app.llm.llm_client import call_llm
from app.security.dependencies import get_current_user
from app.main import limiter



router=APIRouter(prefix="/insights")
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/rejections-by-company")
@limiter.limit("20/minute")
def rejections_by_company(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results =(
        db.query(JobApplication.company,func.count())
        .filter(
            JobApplication.status == JobStatus.Rejected,
            JobApplication.user_id == current_user.id
        )
        .group_by(JobApplication.company).all()
    )
    return [{"company": r[0], "rejections": r[1]} for r in results]


@router.get("/rejection-summary")
@limiter.limit("10/minute")
def rejection_summary(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = (
        db.query(JobApplication.company, func.count())
        .filter(
            JobApplication.status == JobStatus.Rejected,
            JobApplication.user_id == current_user.id
        )
        .group_by(JobApplication.company)
        .all()
    )

    data = [{"company": r[0], "rejections": r[1]} for r in results]

    summary = generate_insight_summary(data)

    return {
        "summary": summary,
        "data": data
    }


@router.get("/rejection-patterns")
@limiter.limit("10/minute")
def rejection_patterns(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobs = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()
    patterns = analyze_rejection_patterns(jobs)
    return {"patterns": patterns}


@router.get("/natural-language")
@limiter.limit("3/minute")
def natural_language_insights(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobs = db.query(JobApplication).filter(
        JobApplication.user_id == current_user.id
    ).all()

    prompt = build_insight_prompt(jobs)
    ai_summary = call_llm(prompt)

    return {
        "summary": ai_summary
    }



@router.get("/job/{job_id}")
@limiter.limit("15/minute")
def job_specific_insight(
    request: Request,
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobApplication).filter(
        JobApplication.id == job_id,
        JobApplication.user_id == current_user.id
    ).first()

    if not job:
        return {"insight": "Job not found."}

    previous_rejections = (
        db.query(JobApplication)
        .filter(
            JobApplication.company == job.company,
            JobApplication.role == job.role,
            JobApplication.status == JobStatus.Rejected,
            JobApplication.id != job.id,
            JobApplication.user_id == current_user.id
        )
        .count()
    )

    insight = generate_job_insight(job, previous_rejections)

    return {"insight": insight}
