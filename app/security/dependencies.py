from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.database import SessionLocal
from app.models.user import User
from app.security.jwt import verify_access_token


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Authentication dependency that:
    1. Extracts JWT token from HTTP-only cookie
    2. Decodes and validates JWT (including expiration)
    3. Loads user from database
    4. Blocks unauthorized access with 401 errors
    """
    # Step 1: Extract token from cookie
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    # Step 2: Decode JWT and validate (includes expiration check)
    payload = verify_access_token(token)
    
    # Block access if token is invalid or expired
    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    # Extract user identifier from token
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )

    # Step 3: Load user from database
    user = db.query(User).filter(User.email == email).first()
    
    # Step 4: Block access if user doesn't exist
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user