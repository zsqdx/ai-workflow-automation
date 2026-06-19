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

## SQS Listener and Workflow Execution

Workflow execution is asynchronous:

1. A workflow run is created with status `PENDING`.
2. An SQS message is sent with `workflow_run_id` only.
3. The workflow execution listener receives the message.
4. The listener loads the workflow run from the repository.
5. The listener checks workflow run status for idempotency.
6. `RefundWorkflow` runs for `REFUND_WORKFLOW`.
7. The workflow run becomes `SUCCEEDED` or `FAILED`.
8. The SQS message is deleted only after successful processing.

SQS carries the reference. The repository stores the full execution state.
The SQS message body contains only:

```json
{
  "workflow_run_id": "run_refund_123"
}
```

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
- `LISTENER_RUN_ONCE`, set to `true` to process one polling batch

Do not commit AWS credentials or the queue URL.

Send a test workflow run message:

```bash
python test_send_workflow_run_message.py
```

Run the listener continuously:

```bash
python -m app.listeners.workflow_execution_listener
```

Run one listener polling batch:

```bash
$env:LISTENER_RUN_ONCE = "true"
python -m app.listeners.workflow_execution_listener
```

Reflection answers:

1. We send only `workflow_run_id` so the SQS message stays small and stable.
2. The repository is the source of truth because it stores the latest workflow run state and input.
3. `SQSService` should not update workflow run status because its only responsibility is moving messages.
4. The listener checks workflow run status before running `RefundWorkflow` to avoid duplicate execution.
5. The listener deletes an SQS message only after workflow success so failed work can be retried.
6. Processing the same refund workflow twice could issue a duplicate refund or send duplicate customer updates.
7. Synchronous workflow execution inside the listener is acceptable because the async boundary is between the API and SQS.
8. A DLQ helps debug failed workflow executions by keeping messages that exceed retry limits.
9. In production, monitor messages received, workflows started, workflows succeeded, workflows failed, duplicates skipped, messages deleted, visible messages, not-visible messages, oldest message age, and DLQ depth.

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
