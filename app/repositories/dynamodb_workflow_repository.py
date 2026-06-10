import os
from datetime import datetime, timezone
from typing import List, Optional

import boto3

from app.models.workflow import WorkflowDefinition
from app.schemas.workflow import (
    WorkflowStatus,
    WorkflowStepCreate,
    WorkflowStepType,
)


class DynamoDBWorkflowRepository:
    def __init__(self):
        self.table_name = os.getenv("WORKFLOW_TABLE_NAME") or "workflow_definitions"
        self.region_name = os.getenv("AWS_REGION") or "us-west-2"

        dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
        self.table = dynamodb.Table(self.table_name)

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        now = datetime.now(timezone.utc).isoformat()
        item = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "status": workflow.status.value,
            "trigger_examples": workflow.trigger_examples,
            "steps": [
                {
                    "name": step.name,
                    "type": step.type.value,
                    "tool_name": step.tool_name,
                }
                for step in workflow.steps
            ],
            "created_at": now,
            "updated_at": now,
        }

        self.table.put_item(Item=item)
        return workflow

    def find_by_id(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        response = self.table.get_item(Key={"workflow_id": workflow_id})
        item = response.get("Item")
        if item is None:
            return None

        return self._to_workflow_definition(item)

    def find_all(self) -> List[WorkflowDefinition]:
        workflows = []
        scan_kwargs = {}

        while True:
            response = self.table.scan(**scan_kwargs)
            workflows.extend(
                self._to_workflow_definition(item)
                for item in response.get("Items", [])
            )

            last_evaluated_key = response.get("LastEvaluatedKey")
            if not last_evaluated_key:
                return workflows

            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

    def _to_workflow_definition(self, item: dict) -> WorkflowDefinition:
        return WorkflowDefinition(
            workflow_id=item["workflow_id"],
            name=item["name"],
            description=item.get("description"),
            version=int(item["version"]),
            status=WorkflowStatus(item["status"]),
            trigger_examples=item.get("trigger_examples", []),
            steps=[
                WorkflowStepCreate(
                    name=step["name"],
                    type=WorkflowStepType(step["type"]),
                    tool_name=step.get("tool_name"),
                )
                for step in item.get("steps", [])
            ],
        )
