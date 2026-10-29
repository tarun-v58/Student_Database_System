from typing import Annotated

from fastapi import Depends
from redis import Redis
from rq import Queue
from sqlalchemy.orm import Session

from app.database import get_db
from app.job_queue import get_redis, get_report_queue
from app.repositories.student_repository import StudentRepository
from app.services.health_service import HealthService
from app.services.report_service import ReportService
from app.services.student_service import StudentService

DbSession = Annotated[Session, Depends(get_db)]


def get_student_repository(db: DbSession) -> StudentRepository:
    return StudentRepository(db)


def get_student_service(
    repository: Annotated[StudentRepository, Depends(get_student_repository)],
) -> StudentService:
    return StudentService(repository)


StudentServiceDep = Annotated[StudentService, Depends(get_student_service)]


def get_report_service(
    queue: Annotated[Queue, Depends(get_report_queue)],
) -> ReportService:
    return ReportService(queue)


ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]


def get_health_service(
    db: DbSession,
    redis: Annotated[Redis, Depends(get_redis)],
) -> HealthService:
    return HealthService(db, redis)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]