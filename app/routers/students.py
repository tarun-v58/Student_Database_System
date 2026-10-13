from fastapi import APIRouter, BackgroundTasks, Response, status
from app.dependencies import StudentServiceDep
from app.schemas import StudentCreate, StudentResponse, StudentUpdate
from app.tasks import send_welcome_email, write_audit_log

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


@router.get("", response_model=list[StudentResponse])
def list_students(service: StudentServiceDep, department: str | None = None):
    return service.list_students(department)


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