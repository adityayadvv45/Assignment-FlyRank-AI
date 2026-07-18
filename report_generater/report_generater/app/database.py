"""
database.py
-----------
Sets up the SQLAlchemy engine, session factory, and declarative Base.

SQLite is used because it's a single file (sales.db) with zero setup -
perfect for a small internship-style project. No external DB server needed.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database file lives at the project root as "sales.db"
SQLALCHEMY_DATABASE_URL = "sqlite:///./sales.db"

# check_same_thread=False is required for SQLite when it's accessed from
# more than one thread (FastAPI's BackgroundTasks run in a worker thread).
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each request/background task gets its own Session from this factory.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this Base.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session and guarantees it's closed
    afterwards, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
