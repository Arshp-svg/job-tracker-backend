from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.database.database import Base


class JobStatus(str, PyEnum):
    Applied = "Applied"
    Interview = "Interview"
    Rejected = "Rejected"
    Offer = "Offer"


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    user = relationship("User")
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.Applied)
    notes = Column(String, default="")
    needs_follow_up = Column(Boolean, default=False)
    applied_date = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now)