from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import SessionLocal
from app.models.job import JobApplication, JobStatus
from app.agents.follow_up_agent import evaluate_follow_up,generate_follow_up_email
from app.security.dependencies import get_current_user
from app.models.user import User
from app.main import limiter
from fastapi import Request
from app.schemas.job_schemas import JobCreateRequest

router = APIRouter(prefix="/jobs")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", status_code=201)
@limiter.limit("20/minute")
def add_job(
    request: Request,
    job_data: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    previous_rejections = (
        db.query(JobApplication)
        .filter(
            JobApplication.company == job_data.company,
            JobApplication.role == job_data.role,
            JobApplication.status == JobStatus.Rejected,
            JobApplication.user_id == current_user.id
        )
        .count()
    )

    job = JobApplication(
        company=job_data.company,
        role=job_data.role,
        status=job_data.status,
        notes=job_data.notes,
        user_id=current_user.id
    )

    job.needs_follow_up = evaluate_follow_up(job)

    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        print(f"Database error: {str(e)}")  # Log the actual error
        raise HTTPException(status_code=500, detail=f"Could not save job: {str(e)}")

    return {
        "job": job,
        "needs_follow_up": evaluate_follow_up(job),
        "previous_rejections": previous_rejections,
        "warning": previous_rejections > 0
    }
    
    
    
@router.get("")
@limiter.limit("30/minute")
def get_jobs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    jobs = (
        db.query(JobApplication)
        .filter(JobApplication.user_id == current_user.id)
        .all()
    )

    response = []
    for job in jobs:
        needs_follow_up = evaluate_follow_up(job)

        response.append({
            "id": job.id,
            "company": job.company,
            "role": job.role,
            "status": job.status.value if hasattr(job.status, "value") else job.status,
            "notes": job.notes,
            "needs_follow_up": needs_follow_up
        })

    return response


@router.get("/{job_id}/follow-up-email")
def get_follow_up_email(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    job = db.query(JobApplication).get(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not evaluate_follow_up(job):
        raise HTTPException(status_code=400, detail="Follow-up not needed yet")

    email = generate_follow_up_email(job.company, job.role)

    return {"email": email}