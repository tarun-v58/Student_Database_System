from app.repositories.student_repository import StudentRepository
from app.schemas import StudentCreate, StudentResponse, StudentUpdate, StudentPage
from app.exceptions import DuplicateEmailError, EmptyUpdateError, StudentNotFoundError
import math


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

    def list_students(
        self,
        *,
        department: str | None = None,
        search: str | None = None,
        sort: str = "id",
        order: str = "asc",
        page: int = 1,
        limit: int = 20,
    ) -> StudentPage:
        search = search.strip() if search else None
        students, total = self.repository.list_page(
            department=department,
            search=search or None,
            sort=sort,
            order=order,
            page=page,
            limit=limit,
        )
        return StudentPage(
            items=[StudentResponse.model_validate(s) for s in students],
            total=total,
            page=page,
            limit=limit,
            pages=math.ceil(total / limit),
        )


    def update_student(self, student_id: int, data: StudentUpdate) -> StudentResponse:
        changes = data.model_dump(exclude_unset=True)
        if not changes:
            raise EmptyUpdateError()
        updated = self.repository.update(student_id, changes)
        if updated is None:
            raise StudentNotFoundError(student_id)
        return updated

    def delete_student(self, student_id: int) -> None:
        if not self.repository.delete(student_id):
            raise StudentNotFoundError(student_id)