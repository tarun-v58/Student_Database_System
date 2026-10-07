from app.exceptions import DuplicateEmailError, StudentNotFoundError
from app.repositories.student_repository import StudentRepository
from app.schemas import StudentCreate, StudentResponse, StudentUpdate


class StudentService:
    def __init__(self, repository: StudentRepository) -> None:
        self.repository = repository

    def create_student(self, data: StudentCreate) -> StudentResponse:
        if self.repository.get_by_email(data.email):
            raise DuplicateEmailError(data.email)
        return self.repository.add(data)

    def get_student(self, student_id: int) -> StudentResponse:
        student = self.repository.get(student_id)
        if student is None:
            raise StudentNotFoundError(student_id)
        return student

    def list_students(self, department: str | None = None) -> list[StudentResponse]:
        return self.repository.list_all(department)

    def update_student(self, student_id: int, data: StudentUpdate) -> StudentResponse:
        changes = data.model_dump(exclude_unset=True)
        updated = self.repository.update(student_id, changes)
        if updated is None:
            raise StudentNotFoundError(student_id)
        return updated

    def delete_student(self, student_id: int) -> None:
        if not self.repository.delete(student_id):
            raise StudentNotFoundError(student_id)