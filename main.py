from typing import Any
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="Task API", version="1.0")


# Custom validation error handler returning 400 with a clean JSON error message
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation failed", "details": exc.errors()},
    )


# In-memory tasks store
tasks = [
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
def get_task(id: int):
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
