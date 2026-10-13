"""
Prompt 2 (Rematch - Improved Specification):

"Build an in-memory CRUD REST API using FastAPI in Python.
The API must satisfy the following strict requirements:
1. Data storage: In-memory list pre-seeded with 3 task dictionaries: id 1 ('Buy groceries', done=False), id 2 ('Read a book', done=True), id 3 ('Write code', done=False).
2. Endpoints:
   - GET /: Returns JSON { 'name': 'Task API', 'version': '1.0', 'endpoints': ['/tasks'] }
   - GET /health: Returns JSON { 'status': 'ok' }
   - GET /tasks: Returns all tasks as a JSON array.
   - GET /tasks/{id}: Returns the task with the given id. If not found, return HTTP 404 with JSON { 'error': 'Task {id} not found' }.
   - POST /tasks: Accepts JSON body { 'title': '...' }. Must return HTTP 201 Created with the new task having next auto-incremented ID and done=False. If title is missing or empty string, return HTTP 400 Bad Request with JSON error message { 'error': 'Title is required and cannot be empty' }.
   - PUT /tasks/{id}: Replaces/updates title and/or done status. Returns HTTP 200 with updated task. If id not found, return HTTP 404 with JSON { 'error': 'Task {id} not found' }. If request body is empty or invalid, return HTTP 400 with { 'error': 'Request body cannot be empty' }.
   - DELETE /tasks/{id}: Deletes the task. Returns HTTP 204 No Content with empty body. If id not found, return HTTP 404 with JSON { 'error': 'Task {id} not found' }.
3. Error payload consistency: All 4xx errors MUST return JSON with the key 'error' rather than FastAPI's default 'detail'. Override FastAPI's RequestValidationError to return 400 instead of 422 with { 'error': 'Validation failed' }.
4. Swagger documentation: Enabled at /docs with descriptive tags and summaries."
"""

from typing import Any, Optional
from fastapi import FastAPI, Path, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API",
    version="1.0",
    docs_url="/docs",
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation failed", "details": exc.errors()},
    )


tasks: list[dict[str, Any]] = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write code", "done": False},
]


def get_next_id() -> int:
    return max([t["id"] for t in tasks], default=0) + 1


@app.get("/")
def get_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health")
def get_health():
    return {"status": "ok"}


@app.get("/tasks")
def get_tasks():
    return tasks


@app.get("/tasks/{id}")
def get_task(id: int = Path(...)):
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})


@app.post("/tasks", status_code=201)
def create_task(payload: dict[str, Any]):
    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})
    title = payload.get("title")
    if title is None or not isinstance(title, str) or title.strip() == "":
        return JSONResponse(
            status_code=400,
            content={"error": "Title is required and cannot be empty"},
        )

    new_task = {
        "id": get_next_id(),
        "title": title.strip(),
        "done": False,
    }
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{id}")
def update_task(id: int, payload: dict[str, Any]):
    if not isinstance(payload, dict) or not payload:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body cannot be empty"},
        )

    task_index = -1
    for idx, t in enumerate(tasks):
        if t["id"] == id:
            task_index = idx
            break

    if task_index == -1:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    current_task = tasks[task_index]
    if "title" in payload:
        title_val = payload["title"]
        if title_val is None or not isinstance(title_val, str) or title_val.strip() == "":
            return JSONResponse(
                status_code=400,
                content={"error": "Title cannot be empty"},
            )
        current_task["title"] = title_val.strip()

    if "done" in payload:
        done_val = payload["done"]
        if not isinstance(done_val, bool):
            return JSONResponse(
                status_code=400,
                content={"error": "Done must be a boolean (true or false)"},
            )
        current_task["done"] = done_val

    tasks[task_index] = current_task
    return current_task


@app.delete("/tasks/{id}", status_code=204)
def delete_task(id: int):
    task_index = -1
    for idx, t in enumerate(tasks):
        if t["id"] == id:
            task_index = idx
            break

    if task_index == -1:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    tasks.pop(task_index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
