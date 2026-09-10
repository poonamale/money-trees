"""
Shared test setup.

Every test gets its OWN fresh, empty database - an in-memory SQLite
db that's created before the test runs and thrown away after. This
matters because tests that share state (e.g. leftover portfolio
contributions from a previous test) produce flaky, order-dependent
results - a classic testing trap.

Two fixtures are provided:
  - db_session:  a raw SQLAlchemy session, for unit-testing crud.py
                  functions directly without going through the API.
  - client:       a FastAPI TestClient wired to use that same test
                  database, for component/integration tests that hit
                  real HTTP endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db

# StaticPool keeps a single shared connection alive for the lifetime
# of the in-memory database - without it, SQLite would create a new
# empty in-memory db on every connection, and your data would vanish
# between queries.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # This is the key trick: FastAPI's dependency injection lets us
    # swap out get_db (which normally points at money_trees.db) for
    # one that points at the test database instead - the route code
    # itself doesn't change at all.
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
