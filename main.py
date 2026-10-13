from typing import Any, Optional
from fastapi import FastAPI, Path, Query, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple, fast in-memory CRUD API for managing your to-do list tasks.",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Custom validation error handler returning 400 with a clean JSON error message
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"error": "Validation failed", "details": exc.errors()},
    )


# Pydantic schemas for rich Swagger documentation
class Task(BaseModel):
    id: int = Field(..., description="Unique task identifier", examples=[1])
    title: str = Field(..., description="Description or title of the task", examples=["Buy milk"])
    done: bool = Field(False, description="Completion status of the task", examples=[False])


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the new task (required, non-empty)", examples=["Buy milk"])


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, description="Updated title of the task", examples=["Buy almond milk"])
    done: Optional[bool] = Field(None, description="Updated completion status", examples=[True])


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message describing what went wrong", examples=["Task 99 not found"])


class ApiInfo(BaseModel):
    name: str = Field(..., examples=["Task API"])
    version: str = Field(..., examples=["1.0"])
    endpoints: list[str] = Field(..., examples=[["/tasks"]])


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


# In-memory tasks store
tasks: list[dict[str, Any]] = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write code", "done": False},
]


def get_next_id() -> int:
    return max([t["id"] for t in tasks], default=0) + 1


@app.get(
    "/",
    response_model=ApiInfo,
    summary="API Root Information",
    description="Returns metadata about the API and its primary endpoints.",
    tags=["General"],
)
def get_root():
    """Returns metadata about the Task API."""
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns the operational status of the server to confirm it is healthy and responsive.",
    tags=["General"],
)
def get_health():
    """Returns server health status."""
    return {"status": "ok"}


@app.get(
    "/tasks",
    response_model=list[Task],
    summary="List all tasks (with optional filtering, search, and pagination)",
    description="Returns tasks. Supports filtering by ?done=true/false, keyword search with ?search=term, and pagination with ?limit=N&offset=N.",
    tags=["Tasks"],
)
def get_tasks(
    done: Optional[bool] = Query(None, description="Filter tasks by completion status"),
    search: Optional[str] = Query(None, description="Search keyword contained in task title"),
    limit: Optional[int] = Query(None, ge=1, description="Maximum number of tasks to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of tasks to skip before starting to collect result"),
):
    """List to-do tasks with optional query filters, search, and pagination."""
    result = tasks

    if done is not None:
        result = [t for t in result if t["done"] is done]

    if search:
        search_lower = search.strip().lower()
        result = [t for t in result if search_lower in t["title"].lower()]

    if offset:
        result = result[offset:]

    if limit is not None:
        result = result[:limit]

    return result


@app.get(
    "/stats",
    summary="Compute task statistics",
    description="Calculates real-time count of total, completed (done), and open (pending) tasks.",
    tags=["Extra Features"],
)
def get_stats():
    """Computes total, done, and open tasks counts."""
    total = len(tasks)
    done_count = sum(1 for t in tasks if t["done"])
    open_count = total - done_count
    return {"total": total, "done": done_count, "open": open_count}


@app.post(
    "/reset",
    summary="Seed & Reset tasks",
    description="Restores the initial seed of 3 example tasks. Perfect for testing and live demos.",
    tags=["Extra Features"],
)
def reset_tasks():
    """Reset the in-memory tasks to default seed."""
    global tasks
    tasks = [
        {"id": 1, "title": "Buy groceries", "done": False},
        {"id": 2, "title": "Read a book", "done": True},
        {"id": 3, "title": "Write code", "done": False},
    ]
    return {"message": "Tasks successfully reset to default seed", "count": len(tasks)}



@app.get(
    "/tasks/{id}",
    response_model=Task,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    summary="Get a single task by ID",
    description="Retrieves a specific task by its numeric ID. Returns 404 if not found.",
    tags=["Tasks"],
)
def get_task(id: int = Path(..., description="The ID of the task to retrieve", examples=[1])):
    """Retrieve a single task by ID."""
    for task in tasks:
        if task["id"] == id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})


@app.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse, "description": "Bad Request - Title is missing or empty"}},
    summary="Create a new task",
    description="Creates a new to-do task with next sequential ID, sets done to false, and returns 201 Created.",
    tags=["Tasks"],
)
def create_task(payload: dict[str, Any]):
    """Create a new task."""
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


@app.put(
    "/tasks/{id}",
    response_model=Task,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid or empty body"},
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Update an existing task",
    description="Replaces a task's title and/or done status with what is provided in the request body.",
    tags=["Tasks"],
)
def update_task(
    id: int = Path(..., description="The ID of the task to update", examples=[1]),
    payload: dict[str, Any] = ...,
):
    """Update title and/or done flag of an existing task."""
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


@app.delete(
    "/tasks/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse, "description": "Task not found"}},
    summary="Delete a task",
    description="Removes a task by its ID. Returns 204 No Content on success, or 404 if not found.",
    tags=["Tasks"],
)
def delete_task(id: int = Path(..., description="The ID of the task to delete", examples=[1])):
    """Delete a task by ID."""
    task_index = -1
    for idx, t in enumerate(tasks):
        if t["id"] == id:
            task_index = idx
            break

    if task_index == -1:
        return JSONResponse(status_code=404, content={"error": f"Task {id} not found"})

    tasks.pop(task_index)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
