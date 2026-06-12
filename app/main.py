import os

from fastapi import FastAPI

from app.api import workflows

APP_ENV = os.getenv("APP_ENV", "local")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

os.environ.setdefault("APP_ENV", APP_ENV)
os.environ.setdefault("AWS_REGION", AWS_REGION)


app = FastAPI(
    title="AI Workflow Automation API",
    version="0.1.0",
)

app.include_router(workflows.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}
