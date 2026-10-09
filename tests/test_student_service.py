from unittest.mock import Mock

import pytest

from app.exceptions import DuplicateEmailError, EmptyUpdateError, StudentNotFoundError
from app.repositories.student_repository import StudentRepository
from app.schemas import StudentCreate, StudentUpdate
from app.services.student_service import StudentService

DATA = StudentCreate(
    name="Rahul Sharma", email="rahul@example.com", department="CSE", age=21
)


@pytest.fixture
def repo():
    return Mock(spec=StudentRepository)


@pytest.fixture
def service(repo):
    return StudentService(repo)


def test_create_saves_student_when_email_is_free(service, repo):
    repo.get_by_email.return_value = None
    repo.add.return_value = "saved student"

    result = service.create_student(DATA)

    assert result == "saved student"
    repo.add.assert_called_once_with(DATA)


def test_create_rejects_duplicate_email(service, repo):
    repo.get_by_email.return_value = object()

    with pytest.raises(DuplicateEmailError):
        service.create_student(DATA)

    repo.add.assert_not_called()


def test_get_missing_student_raises_not_found(service, repo):
    repo.get.return_value = None

    with pytest.raises(StudentNotFoundError):
        service.get_student(7)


def test_update_with_no_fields_raises_and_skips_the_database(service, repo):
    with pytest.raises(EmptyUpdateError):
        service.update_student(1, StudentUpdate())

    repo.update.assert_not_called()


def test_update_passes_only_the_fields_that_were_sent(service, repo):
    repo.update.return_value = "updated student"

    service.update_student(1, StudentUpdate(age=22))

    repo.update.assert_called_once_with(1, {"age": 22})


def test_update_missing_student_raises_not_found(service, repo):
    repo.update.return_value = None

    with pytest.raises(StudentNotFoundError):
        service.update_student(1, StudentUpdate(age=22))


def test_delete_missing_student_raises_not_found(service, repo):
    repo.delete.return_value = False

    with pytest.raises(StudentNotFoundError):
        service.delete_student(1)