from sqlmodel import create_engine, Session
from dotenv import load_dotenv
import os
from fastapi import Depends
from typing import Annotated
from functools import lru_cache


@lru_cache()  # Cache database engine to avoid recreating it on every request
def get_database_engine():
    """Create and return database engine using environment variables."""
    load_dotenv("secrets.env")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    return create_engine(database_url)


engine = get_database_engine()


def get_db():
    """Dependency that yields a database session."""
    with Session(engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]
