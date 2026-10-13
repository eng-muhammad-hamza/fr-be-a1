"""
Prompt 1: Initial AI Prompt (written from memory without looking at original text):

"Write a FastAPI REST API in Python for managing a to-do list in memory.
It should have endpoints to get root info, health status, list all tasks, get a task by id,
create a task, update a task, and delete a task. Validate inputs and return proper HTTP status
codes and JSON errors for not found and bad request."
"""

from typing import Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="AI To-Do API", version="1.0.0")


class TaskCreate(BaseModel):
    title: str
    done: Optional[bool] = False


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


class Task(BaseModel):
    id: int
    title: str
    done: bool


# In-memory storage
tasks: list[dict] = [
    {"id": 1, "title": "Setup repository", "done": True},
    {"id": 2, "title": "Build CRUD API", "done": False},
]


@app.get("/")
def read_root():
    return {"message": "Welcome to AI To-Do API"}


@app.get("/health")
def read_health():
    return {"status": "healthy"}


@app.get("/tasks", response_model=list[Task])
def read_tasks():
    return tasks


@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    if not task.title or task.title.strip() == "":
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    new_id = len(tasks) + 1
    new_task = {"id": new_id, "title": task.title, "done": task.done or False}
    tasks.append(new_task)
    return new_task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskUpdate):
    for task in tasks:
        if task["id"] == task_id:
            if task_update.title is not None:
                task["title"] = task_update.title
            if task_update.done is not None:
                task["done"] = task_update.done
            return task
    raise HTTPException(status_code=404, detail="Task not found")


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    for i, task in enumerate(tasks):
        if task["id"] == task_id:
            tasks.pop(i)
            return
    raise HTTPException(status_code=404, detail="Task not found")
