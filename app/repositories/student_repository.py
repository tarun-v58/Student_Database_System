import itertools
from datetime import datetime

from app.schemas import StudentCreate, StudentResponse


class StudentRepository:
    def __init__(self) -> None:
        self._students: dict[int, StudentResponse] = {}
        self._ids = itertools.count(1)

    def add(self, data: StudentCreate) -> StudentResponse:
        student = StudentResponse(
            id=next(self._ids),
            created_at=datetime.now(),
            **data.model_dump(),
        )
        self._students[student.id] = student
        return student

    def get(self, student_id: int) -> StudentResponse | None:
        return self._students.get(student_id)

    def get_by_email(self, email: str) -> StudentResponse | None:
        for student in self._students.values():
            if student.email.lower() == email.lower():
                return student
        return None

    def list_all(self, department: str | None = None) -> list[StudentResponse]:
        students = list(self._students.values())
        if department:
            students = [
                s for s in students if s.department.lower() == department.lower()
            ]
        return students

    def update(self, student_id: int, changes: dict) -> StudentResponse | None:
        student = self._students.get(student_id)
        if student is None:
            return None
        updated = student.model_copy(update=changes)
        self._students[student_id] = updated
        return updated

    def delete(self, student_id: int) -> bool:
        return self._students.pop(student_id, None) is not None