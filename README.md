# AI Workflow Automation

## Overview

This project is a FastAPI-based backend system for AI workflow automation.
Admin users can define workflow definitions through REST APIs.
This version stores workflow definitions in DynamoDB.

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- boto3
- DynamoDB

## Current APIs

- GET /health
- POST /api/v1/admin/workflows
- GET /api/v1/admin/workflows/{workflow_id}
- GET /api/v1/admin/workflows

## Bonus DynamoDB

This bonus version saves and reads workflow definitions from DynamoDB.

Create this DynamoDB table before running the workflow APIs:

- Table name: `workflow_definitions`
- Primary key: `workflow_id`
- Primary key type: String
- Default region: `us-west-2`

The table name and region can be overridden with environment variables:

- `WORKFLOW_TABLE_NAME`
- `AWS_REGION`

AWS credentials are required through the normal AWS SDK credential chain, such as `aws configure`, environment variables, or an IAM role. Do not put AWS access keys or secret keys in the code.

## How to Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
$env:AWS_REGION = "us-west-2"
$env:WORKFLOW_TABLE_NAME = "workflow_definitions"
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Run with Docker

Build image:

```bash
docker build -t ai-workflow-api .
```

Run container:

```bash
docker run -p 8000:8000 ai-workflow-api
```

Open:

```text
http://localhost:8000/docs
```

Run container in the background:

```bash
docker run -d -p 8000:8000 --name ai-workflow-api-container ai-workflow-api
```

Check running containers:

```bash
docker ps
```

View logs:

```bash
docker logs ai-workflow-api-container
```

Stop container:

```bash
docker stop ai-workflow-api-container
```

Remove container:

```bash
docker rm ai-workflow-api-container
```

Run with environment variables:

```bash
docker run -p 8000:8000 -e APP_ENV=local -e AWS_REGION=us-west-2 ai-workflow-api
```

Run with Docker Compose:

```bash
docker compose up --build
```

Stop Docker Compose:

```bash
docker compose down
```
