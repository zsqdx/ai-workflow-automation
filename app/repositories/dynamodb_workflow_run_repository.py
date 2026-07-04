import os
from typing import Optional

import boto3

from app.models.workflow_run import WorkflowRunDefinition
from app.schemas.workflow_run import WorkflowRunStatus


class DynamoDBWorkflowRunRepository:
    def __init__(self):
        self.table_name = (
            os.getenv("WORKFLOW_RUN_TABLE_NAME")
            or os.getenv("DYNAMODB_WORKFLOW_RUNS_TABLE")
            or "workflow_runs"
        )
        self.region_name = os.getenv("AWS_REGION") or "us-west-2"
        self._table = None

    def save(self, workflow_run: WorkflowRunDefinition) -> WorkflowRunDefinition:
        item = {
            "workflow_run_id": workflow_run.workflow_run_id,
            "ticket_id": workflow_run.ticket_id,
            "workflow_id": workflow_run.workflow_id,
            "workflow_type": workflow_run.workflow_type,
            "customer_id": workflow_run.customer_id,
            "input": workflow_run.input,
            "status": workflow_run.status.value,
            "created_at": workflow_run.created_at,
            "updated_at": workflow_run.updated_at,
            "started_at": workflow_run.started_at,
            "completed_at": workflow_run.completed_at,
            "error_message": workflow_run.error_message,
        }

        self.table.put_item(Item=item)
        return workflow_run

    def find_by_id(self, workflow_run_id: str) -> Optional[WorkflowRunDefinition]:
        response = self.table.get_item(Key={"workflow_run_id": workflow_run_id})
        item = response.get("Item")
        if item is None:
            return None

        return WorkflowRunDefinition(
            workflow_run_id=item["workflow_run_id"],
            ticket_id=item["ticket_id"],
            workflow_id=item["workflow_id"],
            workflow_type=item.get("workflow_type", item.get("job_type", "")),
            customer_id=item["customer_id"],
            input=item.get("input", {}),
            status=WorkflowRunStatus(item["status"]),
            created_at=item["created_at"],
            updated_at=item["updated_at"],
            started_at=item.get("started_at"),
            completed_at=item.get("completed_at"),
            error_message=item.get("error_message"),
        )

    @property
    def table(self):
        if self._table is None:
            dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
            self._table = dynamodb.Table(self.table_name)
        return self._table
