"""
backend/database/engine.py — SQLAlchemy engine and session factory.

Provides:
  - `engine`        : the SQLAlchemy Engine (SQLite by default)
  - `SessionLocal`  : a sessionmaker factory for creating DB sessions
  - `get_db()`      : FastAPI dependency that yields a session and closes it

Usage:
    from backend.database.engine import get_db, engine

    # In a FastAPI route:
    def my_route(db: Session = Depends(get_db)):
        ...

    # Standalone (seed scripts, tests):
    with SessionLocal() as session:
        ...
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.config import settings

logger = logging.getLogger(__name__)

# SQLite needs check_same_thread=False for multi-threaded use (FastAPI).
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

import os
import re

# Auto-create the directory for a SQLite file-based DB (e.g. data/news.db).
_sqlite_path_match = re.match(r"sqlite:///(.+)", settings.database_url)
if _sqlite_path_match:
    _db_file = _sqlite_path_match.group(1)
    _db_dir = os.path.dirname(_db_file)
    if _db_dir:
        os.makedirs(_db_dir, exist_ok=True)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,  # set True to log all SQL (useful for debugging)
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a DB session, close on exit.

    Complexity: O(1) per call.

    Yields:
        Session: an active SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
