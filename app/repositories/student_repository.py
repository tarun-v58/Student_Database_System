from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, select

from app.exceptions import DuplicateEmailError
from app.models import Student
from app.schemas import StudentCreate

SORT_COLUMNS = {
    "id": Student.id,
    "name": Student.name,
    "age": Student.age,
    "created_at": Student.created_at,
}


def _escape_like(text: str) -> str:
    """Make %, _ and \\ in user input match literally inside a LIKE pattern."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class StudentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, data: StudentCreate) -> Student:
        student = Student(**data.model_dump())
        self.db.add(student)
        try:
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise DuplicateEmailError(data.email)
        self.db.refresh(student)
        return student

    def get(self, student_id: int) -> Student | None:
        return self.db.get(Student, student_id)

    def get_by_email(self, email: str) -> Student | None:
        stmt = select(Student).where(func.lower(Student.email) == email.lower())
        return self.db.scalars(stmt).first()

    def list_all(self, department: str | None = None) -> list[Student]:
        stmt = select(Student).order_by(Student.id)
        if department:
            stmt = stmt.where(func.lower(Student.department) == department.lower())
        return list(self.db.scalars(stmt).all())

    def update(self, student_id: int, changes: dict) -> Student | None:
        student = self.db.get(Student, student_id)
        if student is None:
            return None
        for field, value in changes.items():
            setattr(student, field, value)
        self.db.commit()
        self.db.refresh(student)
        return student

    def delete(self, student_id: int) -> bool:
        student = self.db.get(Student, student_id)
        if student is None:
            return False
        self.db.delete(student)
        self.db.commit()
        return True


    def _filtered(self, stmt, department: str | None, search: str | None):
        if department:
            stmt = stmt.where(func.lower(Student.department) == department.lower())
        if search:
            pattern = f"%{_escape_like(search)}%"
            stmt = stmt.where(
                or_(
                    Student.name.ilike(pattern, escape="\\"),
                    Student.email.ilike(pattern, escape="\\"),
                )
            )
        return stmt

    def list_page(
        self,
        *,
        department: str | None,
        search: str | None,
        sort: str,
        order: str,
        page: int,
        limit: int,
    ) -> tuple[list[Student], int]:
        total = self.db.scalar(
            self._filtered(select(func.count()).select_from(Student), department, search)
        )

        column = SORT_COLUMNS[sort]
        primary = column.desc() if order == "desc" else column.asc()
        stmt = (
            self._filtered(select(Student), department, search)
            .order_by(primary, Student.id)
            .limit(limit)
            .offset((page - 1) * limit)
        )
        return list(self.db.scalars(stmt).all()), total