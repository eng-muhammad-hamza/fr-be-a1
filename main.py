from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

# In-memory tasks store
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write code", "done": False},
]


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
