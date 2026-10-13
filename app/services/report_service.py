from redis.exceptions import RedisError
from rq import Queue, Retry

from app.exceptions import QueueUnavailableError, ReportNotFoundError
from app.jobs import generate_student_report
from app.schemas import ReportStatus


def _status_text(job) -> str:
    # Some RQ versions return a plain string, others an enum.
    raw = job.get_status()
    return getattr(raw, "value", raw)


class ReportService:
    def __init__(self, queue: Queue) -> None:
        self.queue = queue

    def request_report(self, department: str | None = None) -> ReportStatus:
        try:
            job = self.queue.enqueue(
                generate_student_report,
                department,
                retry=Retry(max=3, interval=[5, 15, 30]),
                job_timeout=60,
                result_ttl=3600,
                failure_ttl=86400,
            )
        except RedisError:
            raise QueueUnavailableError() from None
        return ReportStatus(job_id=job.id, status="queued")

    def get_report(self, job_id: str) -> ReportStatus:
        try:
            job = self.queue.fetch_job(job_id)
            if job is None:
                raise ReportNotFoundError(job_id)
            status = _status_text(job)
            result = job.return_value() if status == "finished" else None
        except RedisError:
            raise QueueUnavailableError() from None

        error = "Report generation failed" if status == "failed" else None
        return ReportStatus(job_id=job.id, status=status, result=result, error=error)