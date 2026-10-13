from pathlib import Path
from types import SimpleNamespace

import pytest

from app.jobs import generate_student_report
from app.repositories.student_repository import StudentRepository
from app.schemas import StudentCreate
from app.logging_config import request_id_var


@pytest.fixture
def seeded(session_factory, monkeypatch, tmp_path):
    session = session_factory()
    repo = StudentRepository(session)
    repo.add(StudentCreate(name="Rahul Sharma", email="r@x.com", department="CSE", age=21))
    repo.add(StudentCreate(name="Priya Reddy", email="p@x.com", department="ECE", age=20))
    session.close()

    monkeypatch.setattr("app.jobs.SessionLocal", session_factory)
    monkeypatch.setattr(
        "app.jobs.get_settings", lambda: SimpleNamespace(reports_dir=str(tmp_path))
    )
    return tmp_path


def test_report_contains_every_student(seeded):
    result = generate_student_report()

    assert result == {"file": "report_manual.csv", "rows": 2}
    lines = Path(seeded / result["file"]).read_text().splitlines()
    assert lines[0] == "id,name,email,department,age,created_at"
    assert len(lines) == 3


def test_report_can_be_limited_to_one_department(seeded):
    result = generate_student_report("cse")

    assert result["rows"] == 1
    assert "Rahul Sharma" in (seeded / result["file"]).read_text()


def test_running_the_job_twice_gives_the_same_result(seeded):
    first = generate_student_report()
    second = generate_student_report()

    assert first == second
    assert len(list(seeded.glob("*.csv"))) == 1

def test_job_binds_the_request_id_only_while_it_runs(monkeypatch):
    seen = {}

    def fake_write_report(department):
        seen["request_id"] = request_id_var.get()
        return {"file": "x.csv", "rows": 0}

    monkeypatch.setattr("app.jobs._write_report", fake_write_report)

    generate_student_report(request_id="trace-12345678")

    assert seen["request_id"] == "trace-12345678"
    assert request_id_var.get() is None