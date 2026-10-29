import logging
from unittest.mock import Mock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from sqlalchemy.exc import OperationalError

from app.database import get_db
from app.dependencies import get_health_service
from app.main import app
from app.schemas import CheckResult, ReadinessReport
from app.services.health_service import HealthService


def db_down():
    return OperationalError("SELECT 1", {}, Exception("password=secret host=db"))


@pytest.fixture
def db():
    return Mock()


@pytest.fixture
def redis():
    return Mock()


@pytest.fixture
def service(db, redis):
    return HealthService(db, redis)


# ---------- the service ----------

def test_database_check_passes_when_the_query_succeeds(service):
    result = service.check_database()

    assert result.status == "ok"
    assert result.latency_ms >= 0


def test_database_check_reports_failure_without_raising(service, db):
    db.execute.side_effect = db_down()

    assert service.check_database().status == "fail"


def test_redis_check_reports_failure_without_raising(service, redis):
    redis.ping.side_effect = RedisConnectionError("down")

    assert service.check_redis().status == "fail"


def test_readiness_is_ok_when_everything_works(service):
    report = service.readiness()

    assert report.status == "ok"
    assert set(report.checks) == {"database", "redis"}


def test_readiness_is_degraded_when_only_redis_is_down(service, redis):
    redis.ping.side_effect = RedisConnectionError("down")

    report = service.readiness()

    assert report.status == "degraded"
    assert report.checks["database"].status == "ok"
    assert report.checks["redis"].status == "fail"


def test_readiness_is_unavailable_when_the_database_is_down(service, db):
    db.execute.side_effect = db_down()

    assert service.readiness().status == "unavailable"


def test_failure_details_are_not_exposed(service, db):
    db.execute.side_effect = db_down()

    assert "secret" not in service.readiness().model_dump_json()


# ---------- the endpoints ----------

@pytest.fixture
def fake_health(client):
    fake = Mock(spec=HealthService)
    app.dependency_overrides[get_health_service] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_health_service, None)


def report(status, database="ok", redis="ok"):
    return ReadinessReport(
        status=status,
        checks={
            "database": CheckResult(status=database, latency_ms=1.0),
            "redis": CheckResult(status=redis, latency_ms=1.0),
        },
    )


def test_liveness_does_not_depend_on_the_database(client):
    def broken_db():
        raise RuntimeError("database is down")

    app.dependency_overrides[get_db] = broken_db

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_200_when_everything_works(client, fake_health):
    fake_health.readiness.return_value = report("ok")

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_returns_200_but_degraded_when_redis_is_down(client, fake_health):
    fake_health.readiness.return_value = report("degraded", redis="fail")

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["checks"]["redis"]["status"] == "fail"


def test_ready_returns_503_when_the_database_is_down(client, fake_health):
    fake_health.readiness.return_value = report("unavailable", database="fail")

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"


def test_database_health_returns_503_on_failure(client, fake_health):
    fake_health.check_database.return_value = CheckResult(status="fail", latency_ms=5.0)

    assert client.get("/health/db").status_code == 503


def test_database_health_works_against_the_real_test_database(client):
    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_successful_health_probes_log_at_debug_level(client, caplog):
    with caplog.at_level(logging.DEBUG, logger="app.access"):
        client.get("/health")

    records = [r for r in caplog.records if r.name == "app.access"]
    assert records[0].levelno == logging.DEBUG