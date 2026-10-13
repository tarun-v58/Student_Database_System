from app.dependencies import StudentServiceDep
from app.tasks import send_welcome_email, write_audit_log
from typing import Annotated, Literal

from fastapi import APIRouter, BackgroundTasks, Query, Response, status

from app.schemas import StudentCreate, StudentPage, StudentResponse, StudentUpdate

router = APIRouter(prefix="/students", tags=["students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "A student with this email already exists"}},
)
def create_student(
    student: StudentCreate,
    service: StudentServiceDep,
    background_tasks: BackgroundTasks,
):
    created = service.create_student(student)
    # send_welcome_email(created.id, created.name, created.email)   # inline
    background_tasks.add_task(write_audit_log, "student_created", created.id)
    background_tasks.add_task(
        send_welcome_email, created.id, created.name, created.email
    )
    return created

@router.get("", response_model=StudentPage)
def list_students(
    service: StudentServiceDep,
    page: Annotated[int, Query(ge=1, le=100_000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    department: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    sort: Literal["id", "name", "age", "created_at"] = "id",
    order: Literal["asc", "desc"] = "asc",
):
    return service.list_students(
        department=department,
        search=search,
        sort=sort,
        order=order,
        page=page,
        limit=limit,
    )


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, service: StudentServiceDep):
    return service.get_student(student_id)


@router.patch("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, changes: StudentUpdate, service: StudentServiceDep):
    return service.update_student(student_id, changes)


@router.delete(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"description": "Student not found"}},
)
def delete_student(
    student_id: int,
    service: StudentServiceDep,
    background_tasks: BackgroundTasks,
):
    service.delete_student(student_id)
    background_tasks.add_task(write_audit_log, "student_deleted", student_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)