from datetime import datetime, timedelta
from jose import jwt, JWTError
from typing import Optional
from fastapi import HTTPException
import os

# Use environment variable in production
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    expire = datetime.now() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    """
    Verify and decode JWT token.
    Returns payload if valid, None if invalid/expired.
    Automatically validates expiration via 'exp' claim.
    """
    try:
        # jwt.decode automatically validates expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Additional validation: ensure 'sub' (email) exists
        if not payload.get("sub"):
            return None
            
        return payload
    except JWTError as e:
        # Log the error in production for security monitoring
        # logger.warning(f"JWT verification failed: {str(e)}")
        return None
    except Exception:
        return None