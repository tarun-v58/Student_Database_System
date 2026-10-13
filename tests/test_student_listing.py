import pytest

VALID = {
    "name": "Rahul Sharma",
    "email": "rahul@example.com",
    "department": "CSE",
    "age": 21,
}


def make(client, **overrides):
    return client.post("/students", json={**VALID, **overrides})


def seed(client, count=5):
    """Ids 1..5, ages 21,22,20,21,22, departments CSE,ECE,CSE,ECE,CSE."""
    for i in range(1, count + 1):
        make(
            client,
            name=f"Student {i:02d}",
            email=f"s{i}@example.com",
            age=20 + (i % 3),
            department="CSE" if i % 2 else "ECE",
        )


def test_default_response_shape(client):
    seed(client)

    body = client.get("/students").json()

    assert len(body["items"]) == 5
    assert (body["total"], body["page"], body["limit"], body["pages"]) == (5, 1, 20, 1)


def test_pagination_splits_results_into_pages(client):
    seed(client)

    first = client.get("/students", params={"limit": 2, "page": 1}).json()
    last = client.get("/students", params={"limit": 2, "page": 3}).json()

    assert [s["name"] for s in first["items"]] == ["Student 01", "Student 02"]
    assert [s["name"] for s in last["items"]] == ["Student 05"]
    assert first["total"] == 5
    assert first["pages"] == 3


def test_page_beyond_the_end_is_empty_but_total_is_correct(client):
    seed(client)

    body = client.get("/students", params={"limit": 2, "page": 9}).json()

    assert body["items"] == []
    assert body["total"] == 5


def test_search_matches_name_or_email_ignoring_case(client):
    make(client, name="Rahul Sharma", email="rahul@example.com")
    make(client, name="Priya Reddy", email="priya@example.com")
    make(client, name="Anil Kumar", email="anil.rahul@example.com")

    body = client.get("/students", params={"search": "RAHUL"}).json()

    assert body["total"] == 2
    assert {s["name"] for s in body["items"]} == {"Rahul Sharma", "Anil Kumar"}


def test_search_treats_percent_sign_literally(client):
    make(client, name="Ana% Lopez", email="ana@example.com")
    make(client, name="Bob Stone", email="bob@example.com")

    body = client.get("/students", params={"search": "%"}).json()

    assert body["total"] == 1
    assert body["items"][0]["name"] == "Ana% Lopez"


def test_sort_uses_id_as_tiebreaker(client):
    seed(client)

    body = client.get("/students", params={"sort": "age", "order": "desc"}).json()

    assert [s["age"] for s in body["items"]] == [22, 22, 21, 21, 20]
    assert [s["id"] for s in body["items"]] == [2, 5, 1, 4, 3]


def test_filter_and_pagination_work_together(client):
    seed(client)

    body = client.get(
        "/students", params={"department": "cse", "limit": 2}
    ).json()

    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["pages"] == 2


@pytest.mark.parametrize(
    "name, value",
    [
        ("page", 0),
        ("limit", 0),
        ("limit", 101),
        ("sort", "password"),
        ("order", "sideways"),
        ("search", ""),
    ],
)
def test_invalid_query_parameters_are_rejected(client, name, value):
    response = client.get("/students", params={name: value})

    assert response.status_code == 422
    body = response.json()
    assert body["error"] == "validation_error"
    assert body["details"][0]["field"] == name