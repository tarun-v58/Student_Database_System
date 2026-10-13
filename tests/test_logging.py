import json
import logging
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.error_handlers import register_error_handlers
from app.logging_config import JsonFormatter
from app.middleware import request_logging_middleware


def make_record(**extra):
    record = logging.LogRecord(
        "app.test", logging.INFO, __file__, 1, "hello %s", ("world",), None
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_json_formatter_writes_one_object_with_extra_fields():
    record = make_record(request_id="abc12345", student_id=7)

    data = json.loads(JsonFormatter().format(record))

    assert data["message"] == "hello world"
    assert data["level"] == "INFO"
    assert data["logger"] == "app.test"
    assert data["request_id"] == "abc12345"
    assert data["student_id"] == 7


def test_json_formatter_includes_the_traceback():
    try:
        1 / 0
    except ZeroDivisionError:
        record = logging.LogRecord(
            "app.test", logging.ERROR, __file__, 1, "boom", (), sys.exc_info()
        )

    data = json.loads(JsonFormatter().format(record))

    assert "ZeroDivisionError" in data["exception"]


def test_json_formatter_uses_null_when_there_is_no_request_id():
    data = json.loads(JsonFormatter().format(make_record(request_id="-")))

    assert data["request_id"] is None


def test_every_response_carries_a_request_id(client):
    response = client.get("/health")

    assert len(response.headers["x-request-id"]) == 32


def test_a_valid_incoming_request_id_is_kept(client):
    response = client.get("/health", headers={"X-Request-ID": "trace-12345678"})

    assert response.headers["x-request-id"] == "trace-12345678"


def test_an_invalid_incoming_request_id_is_replaced(client):
    response = client.get("/health", headers={"X-Request-ID": "bad id!"})

    assert response.headers["x-request-id"] != "bad id!"
    assert len(response.headers["x-request-id"]) == 32

def test_access_log_records_the_path_but_not_the_query_string(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/students", params={"search": "secret-name"})

    records = [r for r in caplog.records if r.name == "app.access"]
    assert len(records) == 1
    assert records[0].path == "/students"
    assert records[0].status_code == 200
    assert "secret-name" not in str(vars(records[0]))


def test_slow_requests_are_logged_as_warnings(client, caplog, monkeypatch):
    monkeypatch.setattr("app.middleware.SLOW_REQUEST_MS", -1)

    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/health")

    records = [r for r in caplog.records if r.name == "app.access"]
    assert records[0].levelno == logging.WARNING


def make_crashing_app():
    mini = FastAPI()
    register_error_handlers(mini)
    mini.middleware("http")(request_logging_middleware)

    @mini.get("/boom")
    def boom():
        raise RuntimeError("secret detail")

    return mini


def test_a_crash_returns_the_request_id_but_no_details():
    with TestClient(make_crashing_app(), raise_server_exceptions=False) as test_client:
        response = test_client.get("/boom", headers={"X-Request-ID": "trace-12345678"})

    assert response.status_code == 500
    assert response.headers["x-request-id"] == "trace-12345678"
    assert "secret detail" not in response.text


def test_a_crash_is_logged_with_its_traceback(caplog):
    with caplog.at_level(logging.ERROR):
        with TestClient(make_crashing_app(), raise_server_exceptions=False) as test_client:
            test_client.get("/boom")

    assert any(r.name == "app.access" and r.status_code == 500 for r in caplog.records)
    assert any(r.exc_info for r in caplog.records)