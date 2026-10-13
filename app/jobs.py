import csv
import logging
from pathlib import Path

from rq import get_current_job
from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.models import Student

# The worker is a separate process and doesn't run main.py, so set up
# logging here too. Phase 16 replaces this.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app.jobs")

COLUMNS = ["id", "name", "email", "department", "age", "created_at"]


def generate_student_report(department: str | None = None) -> dict:
    job = get_current_job()
    job_id = job.id if job else "manual"
    logger.info("Report job %s started (department=%s)", job_id, department)

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

    logger.info("Report job %s finished (%d rows)", job_id, len(students))
    return {"file": path.name, "rows": len(students)}