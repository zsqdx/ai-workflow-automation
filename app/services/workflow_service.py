from uuid import uuid4

from fastapi import HTTPException

from app.models.workflow import WorkflowDefinition
from app.repositories.dynamodb_workflow_repository import (
    DynamoDBWorkflowRepository,
)
from app.schemas.workflow import (
    CreateWorkflowRequest,
    UpdateWorkflowRequest,
    WorkflowResponse,
    WorkflowStatus,
)
from app.services.workflow_definition_validator import (
    workflow_definition_validator,
)


workflow_repository = DynamoDBWorkflowRepository()


class WorkflowService:
    def create_workflow(self, request: CreateWorkflowRequest) -> WorkflowResponse:
        workflow = WorkflowDefinition(
            workflow_id=str(uuid4()),
            name=request.name,
            description=request.description,
            status=WorkflowStatus.DRAFT,
            job_type=self._job_type_for(request.workflow_type),
            workflow_type=request.workflow_type,
            requires_confirmation=request.requires_confirmation,
            min_confidence=request.min_confidence,
            trigger_examples=request.trigger_examples,
            version=1,
            notification_template_id=request.notification_template_id,
            input_schema=request.input_schema.model_dump(),
        )

        self._validate(workflow)
        saved = workflow_repository.save(workflow)
        return self._to_response(saved)

    def update_workflow(
        self,
        workflow_id: str,
        request: UpdateWorkflowRequest,
    ) -> WorkflowResponse:
        existing = workflow_repository.find_by_id(workflow_id)
        if existing is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}",
            )

        workflow = WorkflowDefinition(
            workflow_id=workflow_id,
            name=request.name,
            description=request.description,
            status=existing.status,
            job_type=self._job_type_for(request.workflow_type),
            workflow_type=request.workflow_type,
            requires_confirmation=request.requires_confirmation,
            min_confidence=request.min_confidence,
            trigger_examples=request.trigger_examples,
            version=existing.version + 1,
            notification_template_id=request.notification_template_id,
            input_schema=request.input_schema.model_dump(),
        )

        self._validate(workflow)
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

    def get_workflow_definition(self, workflow_id: str) -> WorkflowDefinition:
        workflow = workflow_repository.find_by_id(workflow_id)
        if workflow is None:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow not found: {workflow_id}",
            )
        return workflow

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

        self._validate(workflow)
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
            workflow_type=workflow.workflow_type,
            requires_confirmation=workflow.requires_confirmation,
            min_confidence=workflow.min_confidence,
            trigger_examples=workflow.trigger_examples,
            notification_template_id=workflow.notification_template_id,
            input_schema=workflow.input_schema,
            version=workflow.version,
        )

    def _job_type_for(self, workflow_type: str) -> str:
        if workflow_type == "REFUND_WORKFLOW":
            return "REFUND_JOB"
        return workflow_type

    def _validate(self, workflow: WorkflowDefinition) -> None:
        try:
            workflow_definition_validator.validate(workflow)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc


workflow_service = WorkflowService()
