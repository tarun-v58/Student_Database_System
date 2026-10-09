from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.error_handlers import register_error_handlers


def test_unknown_url_returns_not_found(client):
    response = client.get("/nothing")

    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_wrong_method_returns_405(client):
    response = client.put("/students/1", json={"name": "Rahul Sharma"})

    assert response.status_code == 405
    assert response.json()["error"] == "method_not_allowed"


def test_unexpected_crash_returns_generic_500():
    mini_app = FastAPI()
    register_error_handlers(mini_app)

    @mini_app.get("/boom")
    def boom():
        raise RuntimeError("secret database password")

    with TestClient(mini_app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": "internal_error",
        "message": "Something went wrong on our side",
    }
    assert "secret" not in response.text