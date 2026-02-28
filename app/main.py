from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
import uuid
import os

from app.database.database import engine
from app.models.job import Base

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.responses import JSONResponse



limiter = Limiter(key_func=get_remote_address)

from app.routes import jobs
from app.routes import insights
from app.routes import auth

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: JSONResponse(
    status_code=429,
    content={"detail": "Rate limit exceeded"}
))

@app.middleware("http")
async def enforce_https(request: Request, call_next):
    # Check if the request is HTTP and enforce HTTPS in production
    if request.headers.get("x-forwarded-proto") == "http" and os.getenv("ENVIRONMENT") == "production":
        url = str(request.url).replace("http://", "https://", 1)
        return RedirectResponse(url=url, status_code=301)
    return await call_next(request)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:3000 https:;"
    )

    return response

app.add_middleware(SlowAPIMiddleware)


app.add_middleware(
    CORSMiddleware,
     allow_origins=[
        "http://localhost:3000",
        "https://job-tracker-sa35.vercel.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Could not create database tables: {e}")

app.include_router(jobs.router)
app.include_router(insights.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "API running"}

@app.get("/health")
async def health_check():
    from app.database.database import SessionLocal
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )
