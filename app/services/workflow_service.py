from uuid import uuid4

from fastapi import HTTPException

from app.models.workflow import WorkflowDefinition
from app.repositories.dynamodb_workflow_repository import DynamoDBWorkflowRepository
from app.schemas.workflow import (
    CreateWorkflowRequest,
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

        try:
            workflow_definition_validator.validate(workflow)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

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

    def _workflow_type_for(self, job_type: str) -> str:
        if job_type == "REFUND_JOB":
            return "REFUND_WORKFLOW"
        return job_type

    def _job_type_for(self, workflow_type: str) -> str:
        if workflow_type == "REFUND_WORKFLOW":
            return "REFUND_JOB"
        return workflow_type

    def _default_input_schema_for(self, workflow_type: str) -> dict:
        if workflow_type != "REFUND_WORKFLOW":
            return {}

        return {
            "required_fields": [
                {
                    "name": "order_id",
                    "type": "string",
                    "description": (
                        "The order ID the customer wants to refund"
                    ),
                    "examples": ["O123", "O456"],
                    "validation_regex": "^O[0-9]+$",
                    "missing_field_question": (
                        "Please provide your order ID so we can process "
                        "your refund."
                    ),
                },
                {
                    "name": "refund_reason",
                    "type": "string",
                    "description": (
                        "The reason why the customer wants a refund"
                    ),
                    "examples": [
                        "item arrived damaged",
                        "wrong item delivered",
                    ],
                    "min_length": 3,
                    "missing_field_question": (
                        "Please tell us why you are requesting a refund."
                    ),
                },
            ],
            "optional_fields": [],
        }


workflow_service = WorkflowService()
