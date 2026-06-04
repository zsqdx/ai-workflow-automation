from uuid import uuid4

from fastapi import HTTPException

from app.models.workflow import WorkflowDefinition
from app.repositories.workflow_repository import workflow_repository
from app.schemas.workflow import (
    CreateWorkflowRequest,
    WorkflowResponse,
    WorkflowStatus,
)


class WorkflowService:
    def create_workflow(self, request: CreateWorkflowRequest) -> WorkflowResponse:
        if len(request.steps) == 0:
            raise HTTPException(
                status_code=400,
                detail="Workflow must contain at least one step",
            )

        workflow = WorkflowDefinition(
            workflow_id=str(uuid4()),
            name=request.name,
            description=request.description,
            version=1,
            status=WorkflowStatus.DRAFT,
            trigger_examples=request.trigger_examples,
            steps=request.steps,
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

    def _to_response(self, workflow: WorkflowDefinition) -> WorkflowResponse:
        return WorkflowResponse(
            workflow_id=workflow.workflow_id,
            name=workflow.name,
            description=workflow.description,
            version=workflow.version,
            status=workflow.status,
            trigger_examples=workflow.trigger_examples,
            steps=workflow.steps,
        )


workflow_service = WorkflowService()
