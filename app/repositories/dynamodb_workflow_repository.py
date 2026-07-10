import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import boto3

from app.models.workflow import WorkflowDefinition
from app.schemas.workflow import WorkflowStatus


class DynamoDBWorkflowRepository:
    def __init__(self):
        self.table_name = (
            os.getenv("WORKFLOW_TABLE_NAME")
            or os.getenv("DYNAMODB_WORKFLOW_DEFINITIONS_TABLE")
            or "workflow_definitions"
        )
        self.region_name = os.getenv("AWS_REGION") or "us-west-2"
        self._table = None

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        now = datetime.now(timezone.utc).isoformat()
        response = self.table.get_item(Key={"workflow_id": workflow.workflow_id})
        existing_item = response.get("Item") or {}
        created_at = existing_item.get("created_at", now)

        item = {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "status": workflow.status.value,
            "job_type": workflow.job_type,
            "workflow_type": workflow.workflow_type,
            "requires_confirmation": workflow.requires_confirmation,
            "min_confidence": Decimal(str(workflow.min_confidence)),
            "trigger_examples": workflow.trigger_examples,
            "notification_template_id": workflow.notification_template_id,
            "input_schema": workflow.input_schema,
            "created_at": created_at,
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

    @property
    def table(self):
        if self._table is None:
            dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
            self._table = dynamodb.Table(self.table_name)
        return self._table

    def _to_workflow_definition(self, item: dict) -> WorkflowDefinition:
        workflow_type = item.get("workflow_type") or self._workflow_type_for(
            item.get("job_type", "")
        )

        return WorkflowDefinition(
            workflow_id=item["workflow_id"],
            name=item["name"],
            description=item.get("description"),
            status=WorkflowStatus(item["status"]),
            job_type=item.get("job_type") or self._job_type_for(workflow_type),
            workflow_type=workflow_type,
            requires_confirmation=bool(item.get("requires_confirmation", False)),
            min_confidence=float(item.get("min_confidence", 0.7)),
            trigger_examples=item.get("trigger_examples", []),
            notification_template_id=item.get("notification_template_id"),
            input_schema=self._from_dynamodb(
                item.get("input_schema")
                or {"required_fields": [], "optional_fields": []}
            ),
            version=int(item.get("version", 1)),
        )

    def _workflow_type_for(self, job_type: str) -> str:
        if job_type == "REFUND_JOB":
            return "REFUND_WORKFLOW"
        return job_type

    def _job_type_for(self, workflow_type: str) -> str:
        if workflow_type == "REFUND_WORKFLOW":
            return "REFUND_JOB"
        return workflow_type

    def _from_dynamodb(self, value):
        if isinstance(value, Decimal):
            if value % 1 == 0:
                return int(value)
            return float(value)
        if isinstance(value, list):
            return [self._from_dynamodb(item) for item in value]
        if isinstance(value, dict):
            return {
                key: self._from_dynamodb(item)
                for key, item in value.items()
            }
        return value
