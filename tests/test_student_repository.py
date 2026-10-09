import pytest

from app.exceptions import DuplicateEmailError
from app.repositories.student_repository import StudentRepository
from app.schemas import StudentCreate

DATA = StudentCreate(
    name="Rahul Sharma", email="rahul@example.com", department="CSE", age=21
)


def test_database_rejects_duplicate_email_even_without_service_check(db_session):
    repo = StudentRepository(db_session)
    repo.add(DATA)

    with pytest.raises(DuplicateEmailError):
        repo.add(DATA)


def test_session_still_works_after_a_failed_insert(db_session):
    repo = StudentRepository(db_session)
    repo.add(DATA)

    with pytest.raises(DuplicateEmailError):
        repo.add(DATA)

    assert len(repo.list_all()) == 1