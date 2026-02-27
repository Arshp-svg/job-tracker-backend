from pydantic import BaseModel, Field, validator
from app.models.job import JobStatus
from typing import Optional


class JobCreateRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    status: JobStatus
    notes: str = Field(default="", max_length=2000)

    @validator('company', 'role')
    def sanitize_input(cls, v):
        if v:
            return v.strip()
        return v

    class Config:
        use_enum_values = True


class JobUpdateRequest(BaseModel):
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[JobStatus] = None
    notes: Optional[str] = Field(None, max_length=2000)

    @validator('company', 'role')
    def sanitize_input(cls, v):
        if v:
            return v.strip()
        return v

    class Config:
        use_enum_values = True
