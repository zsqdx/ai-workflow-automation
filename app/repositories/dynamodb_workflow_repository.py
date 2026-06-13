import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import boto3

from app.models.workflow import WorkflowDefinition
from app.schemas.workflow import WorkflowStatus


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
            "job_type": workflow.job_type,
            "requires_confirmation": workflow.requires_confirmation,
            "min_confidence": Decimal(str(workflow.min_confidence)),
            "trigger_examples": workflow.trigger_examples,
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
            status=WorkflowStatus(item["status"]),
            job_type=item.get("job_type", ""),
            requires_confirmation=bool(item.get("requires_confirmation", False)),
            min_confidence=float(item.get("min_confidence", 0.0)),
            trigger_examples=item.get("trigger_examples", []),
            version=int(item["version"]),
        )
