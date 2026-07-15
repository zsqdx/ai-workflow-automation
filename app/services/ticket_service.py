from uuid import uuid4

from app.repositories.ticket_repository import ticket_repository
from app.schemas.ticket import (
    CreateTicketRequest,
    SelectedWorkflowResponse,
    TicketResponse,
    TicketStatus,
)
from app.schemas.workflow_run import WorkflowRunStatus
from app.services.field_validation_service import field_validation_service
from app.services.llm_router_service import llm_router_service
from app.services.sqs_service import sqs_service
from app.services.workflow_input_service import workflow_input_service
from app.services.workflow_run_service import workflow_run_service
from app.services.workflow_service import workflow_service


class TicketService:
    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        ticket_id = f"ticket_{uuid4()}"
        ticket = ticket_repository.create_ticket(
            ticket_id=ticket_id,
            customer_id=request.customer_id,
            customer_email=str(request.customer_email),
            message=request.message,
        )

        workflows = workflow_service.list_published_workflows()
        selected = llm_router_service.select_workflow(
            message=request.message,
            workflows=workflows,
        )

        if selected is None:
            ticket_repository.update_status(
                ticket_id=ticket["ticket_id"],
                status=TicketStatus.NO_MATCH.value,
            )
            return TicketResponse(
                ticket_id=ticket_id,
                workflow_run_id=None,
                selected_workflow=None,
                status=TicketStatus.NO_MATCH,
                requires_confirmation=False,
                message="No matching workflow found.",
            )

        workflow_definition = workflow_service.get_workflow_definition(
            selected["workflow_id"]
        )
        selected_workflow = SelectedWorkflowResponse(
            workflow_id=selected["workflow_id"],
            name=selected["name"],
            job_type=selected["job_type"],
            confidence=selected["confidence"],
            reason=selected["reason"],
        )

        extraction_result = workflow_input_service.extract_input(
            workflow_definition=workflow_definition,
            customer_message=request.message,
        )
        validation_result = field_validation_service.validate(
            input_schema=workflow_definition.input_schema,
            extracted_fields=extraction_result["fields"],
            confidence=extraction_result["confidence"],
            min_confidence=workflow_definition.min_confidence,
        )

        requires_confirmation = bool(selected["requires_confirmation"])

        if not validation_result["is_valid"]:
            response_status = TicketStatus.NEEDS_MORE_INFO
            if (
                not validation_result["missing_fields"]
                and validation_result["validation_errors"]
            ):
                response_status = TicketStatus.VALIDATION_FAILED

            ticket_repository.update_status(
                ticket_id=ticket["ticket_id"],
                status=response_status.value,
                selected_workflow_id=workflow_definition.workflow_id,
                selected_workflow_type=workflow_definition.workflow_type,
                selected_workflow_name=workflow_definition.name,
            )
            return TicketResponse(
                ticket_id=ticket["ticket_id"],
                workflow_run_id=None,
                selected_workflow=selected_workflow,
                status=response_status,
                requires_confirmation=requires_confirmation,
                workflow_id=workflow_definition.workflow_id,
                workflow_type=workflow_definition.workflow_type,
                missing_fields=validation_result["missing_fields"],
                validation_errors=validation_result["validation_errors"],
                message=validation_result["message"],
            )

        workflow_run = workflow_run_service.create_workflow_run(
            ticket_id=ticket["ticket_id"],
            workflow_id=workflow_definition.workflow_id,
            workflow_type=workflow_definition.workflow_type,
            customer_id=request.customer_id,
            input={
                "customer_email": str(request.customer_email),
                "raw_message": request.message,
                **extraction_result["fields"],
            },
            notification_template_id=(
                workflow_definition.notification_template_id
            ),
            status=WorkflowRunStatus.PENDING,
        )

        sqs_service.send_workflow_run_message(workflow_run.workflow_run_id)
        ticket_repository.update_status(
            ticket_id=ticket["ticket_id"],
            status=TicketStatus.WORKFLOW_STARTED.value,
            workflow_run_id=workflow_run.workflow_run_id,
            selected_workflow_id=workflow_definition.workflow_id,
            selected_workflow_type=workflow_definition.workflow_type,
            selected_workflow_name=workflow_definition.name,
        )

        return TicketResponse(
            ticket_id=ticket["ticket_id"],
            workflow_run_id=workflow_run.workflow_run_id,
            selected_workflow=selected_workflow,
            status=TicketStatus.WORKFLOW_STARTED,
            requires_confirmation=requires_confirmation,
            workflow_id=workflow_definition.workflow_id,
            workflow_type=workflow_definition.workflow_type,
        )


ticket_service = TicketService()
