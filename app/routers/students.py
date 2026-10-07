from fastapi import APIRouter, Response, status

from app.dependencies import StudentServiceDep
from app.schemas import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, service: StudentServiceDep):
    return service.create_student(student)


@router.get("", response_model=list[StudentResponse])
def list_students(service: StudentServiceDep, department: str | None = None):
    return service.list_students(department)


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, service: StudentServiceDep):
    return service.get_student(student_id)


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, changes: StudentUpdate, service: StudentServiceDep):
    return service.update_student(student_id, changes)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, service: StudentServiceDep):
    service.delete_student(student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)