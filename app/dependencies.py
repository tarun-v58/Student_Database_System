from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.student_repository import StudentRepository
from app.services.student_service import StudentService
from rq import Queue

from app.job_queue import get_report_queue
from app.services.report_service import ReportService


def get_report_service(
    queue: Annotated[Queue, Depends(get_report_queue)],
) -> ReportService:
    return ReportService(queue)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
DbSession = Annotated[Session, Depends(get_db)]


def get_student_repository(db: DbSession) -> StudentRepository:
    return StudentRepository(db)


def get_student_service(
    repository: Annotated[StudentRepository, Depends(get_student_repository)],
) -> StudentService:
    return StudentService(repository)




StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]