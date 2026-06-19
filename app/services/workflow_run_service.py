from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException

from app.models.workflow_run import WorkflowRunDefinition
from app.repositories.dynamodb_workflow_run_repository import (
    DynamoDBWorkflowRunRepository,
)
from app.schemas.workflow_run import WorkflowRunStatus


workflow_run_repository = DynamoDBWorkflowRunRepository()


class WorkflowRunService:
    def create_workflow_run(
        self,
        ticket_id: str,
        workflow_id: str,
        job_type: str,
        customer_id: str,
        workflow_run_id: Optional[str] = None,
        status: WorkflowRunStatus = WorkflowRunStatus.PENDING,
    ) -> WorkflowRunDefinition:
        now = self._now()
        workflow_run = WorkflowRunDefinition(
            workflow_run_id=workflow_run_id or f"run_{uuid4()}",
            ticket_id=ticket_id,
            workflow_id=workflow_id,
            job_type=job_type,
            customer_id=customer_id,
            status=status,
            created_at=now,
            updated_at=now,
        )

        return workflow_run_repository.save(workflow_run)

    def get_workflow_run(self, workflow_run_id: str) -> WorkflowRunDefinition:
        workflow_run = workflow_run_repository.find_by_id(workflow_run_id)
        if workflow_run is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow run not found: {workflow_run_id}",
            )

        return workflow_run

    def update_status(
        self,
        workflow_run_id: str,
        status: str,
        error_message: Optional[str] = None,
    ) -> WorkflowRunDefinition:
        workflow_run = self.get_workflow_run(workflow_run_id)
        next_status = WorkflowRunStatus(status)
        now = self._now()

        workflow_run.status = next_status
        workflow_run.updated_at = now

        if (
            next_status == WorkflowRunStatus.RUNNING
            and workflow_run.started_at is None
        ):
            workflow_run.started_at = now

        if next_status in {
            WorkflowRunStatus.SUCCEEDED,
            WorkflowRunStatus.FAILED,
            WorkflowRunStatus.CANCELLED,
        }:
            workflow_run.completed_at = now

        if error_message is not None:
            workflow_run.error_message = error_message

        return workflow_run_repository.save(workflow_run)

    def should_skip_execution(self, workflow_run_id: str) -> bool:
        workflow_run = self.get_workflow_run(workflow_run_id)
        return workflow_run.status in {
            WorkflowRunStatus.SUCCEEDED,
            WorkflowRunStatus.CANCELLED,
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


workflow_run_service = WorkflowRunService()
