from unittest.mock import Mock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from rq import Queue

from app.exceptions import QueueUnavailableError, ReportNotFoundError
from app.jobs import generate_student_report
from app.services.report_service import ReportService
from app.logging_config import bound_request_id


class FakeJob:
    def __init__(self, id="job-1", status="queued", result=None):
        self.id = id
        self._status = status
        self._result = result

    def get_status(self):
        return self._status

    def return_value(self):
        return self._result


@pytest.fixture
def queue():
    return Mock(spec=Queue)


@pytest.fixture
def service(queue):
    return ReportService(queue)


def test_request_enqueues_the_job_with_retries(service, queue):
    queue.enqueue.return_value = FakeJob(id="job-1")

    result = service.request_report("CSE")

    assert result.job_id == "job-1"
    assert result.status == "queued"
    args, kwargs = queue.enqueue.call_args
    assert args == (generate_student_report, "CSE")
    assert kwargs["retry"].max == 3


def test_request_reports_unavailable_queue(service, queue):
    queue.enqueue.side_effect = RedisConnectionError("down")

    with pytest.raises(QueueUnavailableError):
        service.request_report()


def test_finished_job_returns_its_result(service, queue):
    queue.fetch_job.return_value = FakeJob(
        status="finished", result={"file": "report_job-1.csv", "rows": 2}
    )

    report = service.get_report("job-1")

    assert report.status == "finished"
    assert report.result == {"file": "report_job-1.csv", "rows": 2}
    assert report.error is None


def test_failed_job_hides_the_details(service, queue):
    queue.fetch_job.return_value = FakeJob(status="failed")

    report = service.get_report("job-1")

    assert report.status == "failed"
    assert report.error == "Report generation failed"
    assert report.result is None


def test_unknown_job_raises_not_found(service, queue):
    queue.fetch_job.return_value = None

    with pytest.raises(ReportNotFoundError):
        service.get_report("nope")

def test_request_forwards_the_current_request_id_to_the_job(service, queue):
    queue.enqueue.return_value = FakeJob(id="job-1")

    with bound_request_id("trace-12345678"):
        service.request_report()

    assert queue.enqueue.call_args.kwargs["request_id"] == "trace-12345678"