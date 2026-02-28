from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os

from app.database.database import SessionLocal
from app.models.user import User
from app.security.hashing import hash_password
from app.security.hashing import verify_password
from app.security.jwt import create_access_token
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request
from app.main import limiter
from fastapi.responses import JSONResponse
from app.schemas.auth_schemas import SignupRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

# Check if we're in production
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.post("/signup",status_code=201)
@limiter.limit("5/minute")
def signup(request: Request, signup_data: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == signup_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
        
    hashed_pw=hash_password(signup_data.password)
    user=User(email=signup_data.email, password_hash=hashed_pw)

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not create user"
        )
        
    return {
        "message": "User created successfully",
        "user_id": user.id
    }
    
@router.post("/login")
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # OAuth2PasswordRequestForm uses 'username' field, but we're using email
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
        
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
        
    token = create_access_token(data={"sub": user.email})
    
    response = JSONResponse(content={
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer"
    })
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,  # Only require HTTPS in production
        samesite="none" if IS_PRODUCTION else "lax",  # 'none' for cross-origin in production
        max_age=3600
    )
    return response

@router.post("/logout")
def logout():
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="none" if IS_PRODUCTION else "lax"
    )
    return response