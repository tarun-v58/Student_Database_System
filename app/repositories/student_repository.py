from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import DuplicateEmailError
from app.models import Student
from app.schemas import StudentCreate


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