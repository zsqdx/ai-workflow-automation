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

## ECS Deployment

This deployment runs only the FastAPI API server. It does not run the SQS
listener or any background worker.

Build the Docker image:

```bash
docker build -t ai-workflow-service .
```

Run the API container locally:

```bash
docker run --rm -p 8000:8000 ai-workflow-service
```

Local health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

ECR repository URI placeholder:

```text
<aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/ai-workflow-service
```

Tag the image for ECR:

```bash
docker tag ai-workflow-service:latest <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/ai-workflow-service:latest
```

Push the image to ECR:

```bash
docker push <aws-account-id>.dkr.ecr.<aws-region>.amazonaws.com/ai-workflow-service:latest
```

ECS settings:

- Cluster name: `ai-workflow-cluster`
- Task definition name: `ai-workflow-api-task`
- Service name: `ai-workflow-api-service`
- Container port: `8000`
- Container command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- CloudWatch log group: `/ecs/ai-workflow-api`

CloudWatch Logs Insights query:

```sql
fields @timestamp, @message
| sort @timestamp desc
| limit 20
```

ECS reflection answers:

1. A Docker image is a packaged filesystem and startup configuration for running an application.
2. A container is a running instance of a Docker image.
3. ECR is Amazon Elastic Container Registry, a private registry for Docker images.
4. ECS needs the image in ECR because ECS tasks pull images from a registry, not from a laptop.
5. ECS is Amazon Elastic Container Service, which runs and manages containers on AWS.
6. Fargate is the serverless ECS compute option where AWS manages the container hosts.
7. A task definition is the blueprint for running a container, including image, CPU, memory, ports, roles, environment variables, and logs.
8. An ECS service keeps the desired number of tasks running and replaces unhealthy tasks.
9. The task execution role is used by ECS to pull images and write logs; the task role is used by application code inside the container to call AWS services.
10. The app must listen on `0.0.0.0` so traffic from outside the container can reach it.
11. A CloudWatch log group is a named collection of log streams.
12. A CloudWatch log stream is the ordered logs from one source, such as one ECS task container.
13. Container logs go to stdout/stderr, and the ECS `awslogs` log driver sends them to CloudWatch Logs.

## EKS Deployment

This deployment runs two Kubernetes Deployments on Amazon EKS:

- API pods run FastAPI and expose `GET /health`.
- Listener pod polls SQS, loads `workflow_run` records from DynamoDB, runs `RefundWorkflow`, and deletes SQS messages only after successful processing.

EKS settings:

- ECR image URI: `163596510317.dkr.ecr.us-east-2.amazonaws.com/ai-workflow-service:latest`
- EKS cluster name: `ai-workflow-eks`
- AWS region: `us-east-2`
- Namespace name: `ai-workflow`
- ServiceAccount name: `ai-workflow-sa`
- ConfigMap name: `ai-workflow-config`
- API Deployment name: `ai-workflow-api`
- API Service name: `ai-workflow-api-service`
- Listener Deployment name: `ai-workflow-listener`

Create the EKS cluster:

```bash
eksctl create cluster \
  --name ai-workflow-eks \
  --region us-east-2 \
  --nodes 2 \
  --node-type t3.small \
  --managed
```

Create the IAM policy used by pods:

```bash
aws iam create-policy \
  --policy-name AIWorkflowPodPolicy \
  --policy-document file://infra/ai-workflow-pod-policy.json
```

Enable the EKS OIDC provider:

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster ai-workflow-eks \
  --region us-east-2 \
  --approve
```

Create the Kubernetes ServiceAccount connected to the IAM policy:

```bash
eksctl create iamserviceaccount \
  --name ai-workflow-sa \
  --namespace ai-workflow \
  --cluster ai-workflow-eks \
  --region us-east-2 \
  --attach-policy-arn <AI_WORKFLOW_POLICY_ARN> \
  --approve
```

Apply Kubernetes resources:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl patch configmap ai-workflow-config \
  -n ai-workflow \
  --type merge \
  -p '{"data":{"WORKFLOW_QUEUE_URL":"<WORKFLOW_QUEUE_URL>"}}'
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/api-service.yaml
kubectl apply -f k8s/listener-deployment.yaml
```

The real SQS queue URL is injected during deployment and should not be committed.

Verify:

```bash
kubectl get nodes
kubectl get namespace ai-workflow
kubectl get serviceaccount -n ai-workflow
kubectl describe serviceaccount ai-workflow-sa -n ai-workflow
kubectl get configmap -n ai-workflow
kubectl get deployment -n ai-workflow
kubectl get pods -n ai-workflow
kubectl get service -n ai-workflow
```

Health check:

```bash
curl http://<EXTERNAL_LOAD_BALANCER_DNS>/health
```

Expected result:

```json
{
  "status": "ok"
}
```

SQS message body:

```json
{
  "event_type": "WORKFLOW_RUN_CREATED",
  "workflow_run_id": "run_refund_eks_001"
}
```

DynamoDB `workflow_run` before listener processing:

```json
{
  "workflow_run_id": "run_refund_eks_001",
  "workflow_type": "REFUND_WORKFLOW",
  "status": "PENDING"
}
```

DynamoDB `workflow_run` after listener processing:

```json
{
  "workflow_run_id": "run_refund_eks_001",
  "workflow_type": "REFUND_WORKFLOW",
  "status": "SUCCEEDED"
}
```

Expected listener logs:

```text
Received SQS message
workflow_run_id=run_refund_eks_001
Loaded workflow_run
Current status=PENDING
Updated status to RUNNING
Starting refund workflow
Step 1: Extracting order id
Step 2: Checking order status
Step 3: Issuing refund
Step 4: Generating customer reply
Step 5: Updating ticket status
Updated status to SUCCEEDED
SQS message deleted
```

Duplicate message behavior:

```text
workflow_run_id=run_refund_eks_001 already completed. Skipping duplicate message.
SQS message deleted
```

EKS deployment verification on July 3, 2026:

- LoadBalancer DNS: `aa57ab1f986164d16aca4a09cff84b2d-1504477969.us-east-2.elb.amazonaws.com`
- Health endpoint: `GET /health`
- Health result: `{"status":"ok"}`
- Test workflow run: `run_refund_eks_002`
- Initial DynamoDB status: `PENDING`
- Final DynamoDB status: `SUCCEEDED`
- Duplicate message queue depth after processing: visible `0`, not visible `0`

Listener log excerpt:

```text
Received 1 SQS message(s)
Received SQS message
workflow_run_id=run_refund_eks_002
Loaded workflow_run
Current status=PENDING
Updated status to RUNNING
Starting refund workflow
workflow_run_id=run_refund_eks_002
order_id=O123
Step 1: Extracting order id
Step 2: Checking order status
Step 3: Issuing refund
Step 4: Generating customer reply
Step 5: Updating ticket status
Refund workflow completed
Updated status to SUCCEEDED
SQS message deleted
```

Duplicate message log excerpt:

```text
workflow_run_id=run_refund_eks_002 already completed. Skipping duplicate message.
SQS message deleted
```

Cleanup:

```bash
kubectl delete -f k8s/listener-deployment.yaml
kubectl delete -f k8s/api-service.yaml
kubectl delete -f k8s/api-deployment.yaml
kubectl delete -f k8s/secret.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml

eksctl delete cluster \
  --name ai-workflow-eks \
  --region us-east-2
```

Cleanup confirmation: cleanup was not run yet because the EKS deployment is left active for grading and verification.

EKS reflection answers:

1. A ConfigMap stores non-sensitive configuration values for pods, such as region, table names, and environment names.
2. A ServiceAccount is the Kubernetes identity assigned to pods.
3. Pods need a ServiceAccount so they can receive the correct permissions and, on EKS, assume an IAM role through IRSA.
4. A Deployment manages replicated pods and replaces them when they crash or are updated.
5. A Kubernetes Service gives stable network access to a set of pods.
6. The API needs a Service because users call it over HTTP; the listener does not need one because it only polls SQS.
7. The SQS message only contains `workflow_run_id` so the queue carries a small event reference instead of duplicating workflow state.
8. The listener reads `workflow_run` from DynamoDB because the repository is the source of truth.
9. `workflow_run` status represents the lifecycle of one workflow execution, such as `PENDING`, `RUNNING`, `SUCCEEDED`, or `FAILED`.
10. The listener deletes an SQS message only after success so failed work can be retried.
11. The same AWS IAM user can be reused from a laptop to create infrastructure, but it should not be used inside pods.
12. AWS access keys should not be put inside pods because IAM roles and ServiceAccounts provide safer, revocable, short-lived credentials.
