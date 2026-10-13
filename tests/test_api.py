import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_database():
    """Ensure clean state before each test."""
    client.post("/reset")


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_all_tasks():
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
    assert tasks[0]["id"] == 1
    assert tasks[0]["title"] == "Buy groceries"
    assert tasks[0]["done"] is False


def test_get_single_task():
    response = client.get("/tasks/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "title": "Buy groceries",
        "done": False,
    }


def test_get_task_not_found():
    response = client.get("/tasks/99")
    assert response.status_code == 404
    assert response.json() == {"error": "Task 99 not found"}


def test_create_task():
    response = client.post("/tasks", json={"title": "Buy milk"})
    assert response.status_code == 201
    created = response.json()
    assert created["id"] == 4
    assert created["title"] == "Buy milk"
    assert created["done"] is False

    # Check it shows up in GET /tasks
    list_res = client.get("/tasks")
    assert len(list_res.json()) == 4


def test_create_task_validation():
    # Empty title
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 400
    assert response.json() == {"error": "Title is required and cannot be empty"}

    # Whitespace title
    response_ws = client.post("/tasks", json={"title": "   "})
    assert response_ws.status_code == 400
    assert response_ws.json() == {"error": "Title is required and cannot be empty"}

    # Missing title
    response_missing = client.post("/tasks", json={})
    assert response_missing.status_code == 400
    assert response_missing.json() == {"error": "Title is required and cannot be empty"}


def test_update_task():
    response = client.put("/tasks/1", json={"title": "Buy almond milk", "done": True})
    assert response.status_code == 200
    updated = response.json()
    assert updated["id"] == 1
    assert updated["title"] == "Buy almond milk"
    assert updated["done"] is True


def test_update_task_validation():
    # Empty body
    response = client.put("/tasks/1", json={})
    assert response.status_code == 400
    assert response.json() == {"error": "Request body cannot be empty"}

    # Empty title string
    response_empty = client.put("/tasks/1", json={"title": ""})
    assert response_empty.status_code == 400
    assert response_empty.json() == {"error": "Title cannot be empty"}

    # Non-boolean done
    response_done = client.put("/tasks/1", json={"done": "yes"})
    assert response_done.status_code == 400
    assert response_done.json() == {"error": "Done must be a boolean (true or false)"}

    # Not found
    response_404 = client.put("/tasks/99", json={"title": "Non-existent"})
    assert response_404.status_code == 404
    assert response_404.json() == {"error": "Task 99 not found"}


def test_delete_task():
    response = client.delete("/tasks/1")
    assert response.status_code == 204
    assert response.content == b""

    # Verify task 1 is gone
    get_res = client.get("/tasks/1")
    assert get_res.status_code == 404

    # Verify 404 when deleting again
    del_404 = client.delete("/tasks/1")
    assert del_404.status_code == 404
    assert del_404.json() == {"error": "Task 1 not found"}


def test_extra_stats():
    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json() == {"total": 3, "done": 1, "open": 2}


def test_extra_filtering_and_search():
    res_done = client.get("/tasks?done=true")
    assert res_done.status_code == 200
    assert len(res_done.json()) == 1
    assert res_done.json()[0]["id"] == 2

    res_search = client.get("/tasks?search=code")
    assert res_search.status_code == 200
    assert len(res_search.json()) == 1
    assert res_search.json()[0]["title"] == "Write code"


def test_extra_pagination():
    res_page = client.get("/tasks?limit=2&offset=1")
    assert res_page.status_code == 200
    ids = [t["id"] for t in res_page.json()]
    assert ids == [2, 3]
