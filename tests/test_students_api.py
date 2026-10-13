import pytest

VALID = {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "department": "CSE",
    "age": 21,
}


def make(client, **overrides):
    return client.post("/students", json={**VALID, **overrides})


# ---------- create ----------

def test_create_student(client):
    response = make(client)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "Rahul Sharma"
    assert body["email"] == "rahul@example.com"
    assert "created_at" in body

def test_create_rejects_duplicate_email_ignoring_case(client):
    make(client)

    response = make(client, email="RAHUL@example.com")

    assert response.status_code == 409
    assert response.json()["error"] == "duplicate_email"

def test_list_students_and_filter_by_department(client):
    make(client)
    make(client, name="Priya Reddy", email="priya@example.com", department="ECE", age=20)

    everyone = client.get("/students")
    assert everyone.status_code == 200
    assert everyone.json()["total"] == 2

    ece = client.get("/students", params={"department": "ece"})
    assert ece.status_code == 200
    assert [s["name"] for s in ece.json()["items"]] == ["Priya Reddy"]


@pytest.mark.parametrize(
    "field, value",
    [
        ("email", "not-an-email"),
        ("age", 200),
        ("age", 5),
        ("name", "A"),
        ("name", "   "),
        ("department", ""),
    ],
)
def test_create_rejects_invalid_input(client, field, value):
    response = make(client, **{field: value})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["details"][0]["field"] == field


def test_create_rejects_missing_fields(client):
    response = client.post("/students", json={"name": "Rahul Sharma"})

    assert response.status_code == 422
    fields = {d["field"] for d in response.json()["details"]}
    assert {"email", "department", "age"} <= fields


def test_create_rejects_unknown_field(client):
    response = make(client, id=5)

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


# ---------- read ----------

def test_list_students_and_filter_by_department(client):
    make(client)
    make(client, name="Priya Reddy", email="priya@example.com", department="ECE", age=20)

    everyone = client.get("/students")
    assert everyone.status_code == 200
    assert everyone.json()["total"] == 2

    ece = client.get("/students", params={"department": "ece"})
    assert ece.status_code == 200
    assert [s["name"] for s in ece.json()["items"]] == ["Priya Reddy"]



def test_get_student(client):
    make(client)

    response = client.get("/students/1")

    assert response.status_code == 200
    assert response.json()["email"] == "rahul@example.com"


def test_get_missing_student(client):
    response = client.get("/students/99999")

    assert response.status_code == 404
    assert response.json()["error"] == "student_not_found"


def test_get_student_with_non_integer_id(client):
    response = client.get("/students/abc")

    assert response.status_code == 422
    assert response.json()["error"] == "validation_error"


# ---------- update ----------

def test_patch_changes_only_the_fields_sent(client):
    make(client)

    response = client.patch("/students/1", json={"age": 22})

    assert response.status_code == 200
    body = response.json()
    assert body["age"] == 22
    assert body["name"] == "Rahul Sharma"
    assert body["department"] == "CSE"


def test_patch_with_empty_body_is_rejected(client):
    make(client)

    response = client.patch("/students/1", json={})

    assert response.status_code == 422
    assert response.json()["error"] == "empty_update"


def test_patch_missing_student(client):
    response = client.patch("/students/99999", json={"age": 21})

    assert response.status_code == 404
    assert response.json()["error"] == "student_not_found"


def test_patch_cannot_change_email(client):
    make(client)

    response = client.patch("/students/1", json={"email": "new@example.com"})

    assert response.status_code == 422


# ---------- delete ----------

def test_delete_student(client):
    make(client)

    response = client.delete("/students/1")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/students/1").status_code == 404


def test_delete_missing_student(client):
    response = client.delete("/students/99999")

    assert response.status_code == 404
    assert response.json()["error"] == "student_not_found"