"""
Database setup for Money Trees.

Uses SQLite for simplicity - it's just a local file (money_trees.db),
no separate database server needed. Perfect for a portfolio project.
If you later want to deploy this publicly, swapping to Postgres is a
one-line change to SQLALCHEMY_DATABASE_URL below.

Coming from other languages: SQLAlchemy is Python's most common ORM -
similar in spirit to Hibernate (Java) or Sequelize/TypeORM (JS).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./money_trees.db"

# check_same_thread=False is SQLite-specific - it allows the same
# connection to be shared across threads, which FastAPI needs.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class every table model will inherit from.
Base = declarative_base()


def get_db():
    """
    Dependency that provides a fresh database session per-request,
    and always closes it afterwards - even if an error occurs partway
    through a request. FastAPI calls this automatically via Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
