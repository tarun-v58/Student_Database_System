from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import get_db
from app.main import app

TEST_DB_NAME = "student_test_db"
SCHEMA_FILE = Path(__file__).resolve().parent.parent / "docs" / "schema.sql"


@pytest.fixture(scope="session")
def engine():
    """One engine for the whole test run, pointed at the TEST database."""
    settings = get_settings()
    if settings.db_name == TEST_DB_NAME:
        raise RuntimeError("DB_NAME must not be the test database")

    test_engine = create_engine(
        settings.database_url.set(database=TEST_DB_NAME),
        pool_pre_ping=True,
    )
    with test_engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS students")
        conn.exec_driver_sql(SCHEMA_FILE.read_text())

    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine):
    """Empties the table before every test, then hands out sessions."""
    with engine.begin() as conn:
        conn.exec_driver_sql("TRUNCATE students RESTART IDENTITY")
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def db_session(session_factory):
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(session_factory):
    def override_get_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()