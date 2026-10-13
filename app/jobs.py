import csv
import logging
from pathlib import Path

from rq import get_current_job
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.logging_config import bound_request_id, configure_logging
from app.models import Student

# The worker is its own process and never imports main.py, so it configures
# logging itself.
_settings = get_settings()
configure_logging(_settings.log_level, _settings.log_json)
logger = logging.getLogger("app.jobs")

COLUMNS = ["id", "name", "email", "department", "age", "created_at"]


def generate_student_report(
    department: str | None = None, request_id: str | None = None
) -> dict:
    with bound_request_id(request_id):
        try:
            return _write_report(department)
        except Exception:
            logger.exception("Report job failed", extra={"department": department})
            raise


def _write_report(department: str | None) -> dict:
    job = get_current_job()
    job_id = job.id if job else "manual"
    logger.info(
        "Report job %s started",
        job_id,
        extra={"job_id": job_id, "department": department},
    )

    db = SessionLocal()
    try:
        stmt = select(Student).order_by(Student.id)
        if department:
            stmt = stmt.where(func.lower(Student.department) == department.lower())
        students = db.scalars(stmt).all()
    finally:
        db.close()

    reports_dir = Path(get_settings().reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"report_{job_id}.csv"

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for s in students:
            writer.writerow(
                [s.id, s.name, s.email, s.department, s.age, s.created_at.isoformat()]
            )

    logger.info(
        "Report job %s finished (%d rows)",
        job_id,
        len(students),
        extra={"job_id": job_id, "rows": len(students)},
    )
    return {"file": path.name, "rows": len(students)}