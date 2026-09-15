"""
backend/database/init_db.py — Create all database tables.

Run this once before seeding the database. Safe to call multiple times
(SQLAlchemy uses CREATE TABLE IF NOT EXISTS semantics).

Usage:
    python -m backend.database.init_db
"""

import logging

from backend.database.engine import engine
from backend.models.models import Base  # noqa: F401  — registers all models

logger = logging.getLogger(__name__)


def create_tables() -> None:
    """Create all ORM-mapped tables in the database.

    Complexity: O(T) where T = number of table definitions.

    Uses SQLAlchemy metadata to issue DDL statements. Safe to re-run.
    """
    logger.info("[init_db.create_tables] Creating all tables…")
    Base.metadata.create_all(bind=engine)
    logger.info("[init_db.create_tables] Done.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_tables()
    print("All tables created.")
