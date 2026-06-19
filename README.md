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
- POST /api/v1/admin/workflows/{workflow_id}/publish
- GET /api/v1/admin/workflows
- POST /api/v1/tickets

## LLM Router

The ticket API uses the OpenAI Responses API to route customer messages to a
published workflow. The router reads credentials and model configuration from
environment variables.

Required:

- `OPENAI_API_KEY`

Optional:

- `OPENAI_MODEL`, default `gpt-4o-mini`

Do not put API keys in code, README files, logs, Docker images, or Git commits.

## SQS Refund Worker

Refund workflow execution is asynchronous:

1. A workflow run is created with status `PENDING`.
2. A refund execution message is sent to AWS SQS.
3. The refund worker receives the message.
4. The worker checks workflow run status for idempotency.
5. `RefundJob` runs.
6. The workflow run becomes `SUCCEEDED` or `FAILED`.
7. The SQS message is deleted only after successful processing.

Create an SQS Standard queue:

- Queue name: `ai-workflow-execution-queue`
- Visibility timeout: 30 seconds
- Message retention period: 4 days
- Receive message wait time: 10 seconds

Create a DynamoDB table for workflow run state:

- Table name: `workflow_runs`
- Primary key: `workflow_run_id`
- Primary key type: String

Required environment variables:

- `WORKFLOW_QUEUE_URL`
- `AWS_REGION`

Optional environment variables:

- `WORKFLOW_RUN_TABLE_NAME`, default `workflow_runs`
- `WORKER_RUN_ONCE`, set to `true` to process one polling batch

Do not commit AWS credentials or the queue URL.

Send a test refund message:

```bash
python test_send_refund_message.py
```

Run the worker continuously:

```bash
python -m app.workers.refund_worker
```

Run one worker polling batch:

```bash
$env:WORKER_RUN_ONCE = "true"
python -m app.workers.refund_worker
```

Reflection answers:

1. `SQSService` should not update workflow run status because its only responsibility is moving messages.
2. The worker checks workflow run status before running `RefundJob` to avoid duplicate execution.
3. The worker deletes an SQS message only after job success so failed work can be retried.
4. Processing the same refund twice could issue a duplicate refund or send duplicate customer updates.
5. A DLQ helps debug failed messages by keeping messages that exceed retry limits.
6. In production, monitor messages received, jobs started, jobs succeeded, jobs failed, duplicates skipped, messages deleted, visible messages, not-visible messages, oldest message age, and DLQ depth.

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
$env:WORKFLOW_RUN_TABLE_NAME = "workflow_runs"
$env:WORKFLOW_QUEUE_URL = "<your-sqs-queue-url>"
$env:OPENAI_API_KEY = "<your-openai-api-key>"
$env:OPENAI_MODEL = "gpt-4o-mini"
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
