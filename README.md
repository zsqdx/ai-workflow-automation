# AI Workflow Automation

## Overview

This project is a FastAPI-based backend system for AI workflow automation.
Admin users can define workflow definitions through REST APIs.
This first version uses in-memory storage, so workflow data is lost when the server restarts.

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- In-memory Python dictionary storage

## Current APIs

- GET /health
- POST /api/v1/admin/workflows
- GET /api/v1/admin/workflows/{workflow_id}
- GET /api/v1/admin/workflows

## How to Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```
