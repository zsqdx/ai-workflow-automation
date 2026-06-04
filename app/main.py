from fastapi import FastAPI

from app.api import workflows


app = FastAPI(
    title="AI Workflow Automation API",
    version="0.1.0",
)

app.include_router(workflows.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
