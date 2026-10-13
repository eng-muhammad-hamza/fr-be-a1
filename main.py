from fastapi import FastAPI

app = FastAPI(title="Task API", version="1.0")


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
