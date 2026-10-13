from unittest.mock import Mock

import pytest

from app.dependencies import get_report_service
from app.exceptions import QueueUnavailableError, ReportNotFoundError
from app.main import app
from app.schemas import ReportStatus
from app.services.report_service import ReportService


@pytest.fixture
def fake_service(client):
    service = Mock(spec=ReportService)
    app.dependency_overrides[get_report_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_report_service, None)


def test_post_returns_202_and_the_job_id(client, fake_service):
    fake_service.request_report.return_value = ReportStatus(
        job_id="job-1", status="queued"
    )

    response = client.post("/reports", json={"department": "CSE"})

    assert response.status_code == 202
    assert response.json()["job_id"] == "job-1"
    fake_service.request_report.assert_called_once_with("CSE")


def test_post_without_a_body_means_all_departments(client, fake_service):
    fake_service.request_report.return_value = ReportStatus(
        job_id="job-1", status="queued"
    )

    response = client.post("/reports")

    assert response.status_code == 202
    fake_service.request_report.assert_called_once_with(None)


def test_post_rejects_unknown_fields(client, fake_service):
    response = client.post("/reports", json={"colour": "red"})

    assert response.status_code == 422


def test_get_returns_the_job_status(client, fake_service):
    fake_service.get_report.return_value = ReportStatus(
        job_id="job-1", status="finished", result={"file": "r.csv", "rows": 2}
    )

    response = client.get("/reports/job-1")

    assert response.status_code == 200
    assert response.json()["result"]["rows"] == 2


def test_get_unknown_job_returns_404(client, fake_service):
    fake_service.get_report.side_effect = ReportNotFoundError("nope")

    response = client.get("/reports/nope")

    assert response.status_code == 404
    assert response.json()["error"] == "report_not_found"


def test_unavailable_queue_returns_503(client, fake_service):
    fake_service.request_report.side_effect = QueueUnavailableError()

    response = client.post("/reports")

    assert response.status_code == 503
    assert response.json()["error"] == "queue_unavailable"