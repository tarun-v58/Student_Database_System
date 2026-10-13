import logging

from app.tasks import send_welcome_email, write_audit_log

VALID = {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "department": "CSE",
    "age": 21,
}


def test_create_schedules_audit_log_and_welcome_email(client, background_task_mocks):
    response = client.post("/students", json=VALID)

    assert response.status_code == 201
    background_task_mocks.audit.assert_called_once_with("student_created", 1)
    background_task_mocks.email.assert_called_once_with(
        1, "Rahul Sharma", "rahul@example.com"
    )


def test_failed_create_schedules_nothing(client, background_task_mocks):
    client.post("/students", json=VALID)
    background_task_mocks.audit.reset_mock()
    background_task_mocks.email.reset_mock()

    response = client.post("/students", json=VALID)

    assert response.status_code == 409
    background_task_mocks.audit.assert_not_called()
    background_task_mocks.email.assert_not_called()


def test_delete_schedules_audit_log(client, background_task_mocks):
    client.post("/students", json=VALID)
    background_task_mocks.audit.reset_mock()

    response = client.delete("/students/1")

    assert response.status_code == 204
    background_task_mocks.audit.assert_called_once_with("student_deleted", 1)


def test_audit_log_writes_a_log_line(caplog):
    with caplog.at_level(logging.INFO, logger="app.tasks"):
        write_audit_log("student_created", 7)

    assert "action=student_created" in caplog.text
    assert "student_id=7" in caplog.text


def test_welcome_email_logs_the_id_but_not_the_address(caplog, monkeypatch):
    monkeypatch.setattr("app.tasks.time.sleep", lambda seconds: None)

    with caplog.at_level(logging.INFO, logger="app.tasks"):
        send_welcome_email(7, "Rahul Sharma", "rahul@example.com")

    assert "student 7" in caplog.text
    assert "rahul@example.com" not in caplog.text