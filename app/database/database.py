from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus
import os
import re


def fix_database_url(url: str) -> str:
    """Fix DATABASE_URL by properly encoding the password if it contains special characters."""
    if url.startswith("sqlite"):
        return url
    
    # Match postgresql://user:password@host:port/database
    pattern = r'^(postgresql(?:\+\w+)?://)([^:]+):([^@]+)@(.+)$'
    match = re.match(pattern, url)
    
    if match:
        protocol, user, password, rest = match.groups()
        # URL-encode the password (and username for safety)
        encoded_user = quote_plus(user)
        encoded_password = quote_plus(password)
        return f"{protocol}{encoded_user}:{encoded_password}@{rest}"
    
    return url


DATABASE_URL = fix_database_url(os.getenv("DATABASE_URL", "sqlite:///./jobs.db"))


if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "connect_timeout": 10,
        }
    )

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
