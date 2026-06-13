from uuid import uuid4

from fastapi import HTTPException

from app.models.workflow import WorkflowDefinition
from app.repositories.dynamodb_workflow_repository import DynamoDBWorkflowRepository
from app.schemas.workflow import (
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowStatus,
)


workflow_repository = DynamoDBWorkflowRepository()


class WorkflowService:
    def create_workflow(self, request: CreateWorkflowRequest) -> WorkflowResponse:
        workflow = WorkflowDefinition(
            workflow_id=str(uuid4()),
            name=request.name,
            description=request.description,
            status=WorkflowStatus.DRAFT,
            job_type=request.job_type,
            requires_confirmation=request.requires_confirmation,
            min_confidence=request.min_confidence,
            trigger_examples=request.trigger_examples,
            version=1,
        )

        saved = workflow_repository.save(workflow)
        return self._to_response(saved)

    def get_workflow(self, workflow_id: str) -> WorkflowResponse:
        workflow = workflow_repository.find_by_id(workflow_id)
        if workflow is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}",
            )

        return self._to_response(workflow)

    def list_workflows(self):
        return [
            self._to_response(workflow)
            for workflow in workflow_repository.find_all()
        ]

    def publish_workflow(self, workflow_id: str) -> WorkflowResponse:
        workflow = workflow_repository.find_by_id(workflow_id)
        if workflow is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}",
            )

        workflow.status = WorkflowStatus.PUBLISHED
        saved = workflow_repository.save(workflow)
        return self._to_response(saved)

    def list_published_workflows(self):
        return [
            workflow
            for workflow in workflow_repository.find_all()
            if workflow.status == WorkflowStatus.PUBLISHED
        ]

    def _to_response(self, workflow: WorkflowDefinition) -> WorkflowResponse:
        return WorkflowResponse(
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            description=workflow.description,
            status=workflow.status,
            job_type=workflow.job_type,
            requires_confirmation=workflow.requires_confirmation,
            min_confidence=workflow.min_confidence,
            trigger_examples=workflow.trigger_examples,
            version=workflow.version,
        )


workflow_service = WorkflowService()
