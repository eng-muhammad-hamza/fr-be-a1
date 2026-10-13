from fastapi import FastAPI

app = FastAPI(title="Task API", version="1.0")


@app.get("/")
def hello():
    return {"message": "Hello, server!"}
