import re
from uuid import uuid4

from app.schemas.ticket import (
    CreateTicketRequest,
    SelectedWorkflowResponse,
    TicketResponse,
    TicketStatus,
)
from app.schemas.workflow_run import WorkflowRunStatus
from app.services.llm_router_service import llm_router_service
from app.services.sqs_service import sqs_service
from app.services.workflow_run_service import workflow_run_service
from app.services.workflow_service import workflow_service


class TicketService:
    def create_ticket(self, request: CreateTicketRequest) -> TicketResponse:
        ticket_id = f"ticket_{uuid4()}"
        workflows = workflow_service.list_published_workflows()
        selected = llm_router_service.select_workflow(
            message=request.message,
            workflows=workflows,
        )

        if selected is None:
            return TicketResponse(
                ticket_id=ticket_id,
                workflow_run_id=None,
                selected_workflow=None,
                status=TicketStatus.NO_MATCH,
                requires_confirmation=False,
            )

        requires_confirmation = bool(selected["requires_confirmation"])
        ticket_status = (
            TicketStatus.WAITING_FOR_CONFIRMATION
            if requires_confirmation
            else TicketStatus.PENDING
        )
        workflow_run_status = (
            WorkflowRunStatus.WAITING_FOR_CONFIRMATION
            if requires_confirmation
            else WorkflowRunStatus.PENDING
        )
        workflow_run = workflow_run_service.create_workflow_run(
            ticket_id=ticket_id,
            workflow_id=selected["workflow_id"],
            job_type=selected["job_type"],
            customer_id=request.customer_id,
            status=workflow_run_status,
        )

        if (
            workflow_run.status == WorkflowRunStatus.PENDING
            and selected["job_type"] == "REFUND_JOB"
        ):
            sqs_service.send_refund_workflow_message(
                workflow_run_id=workflow_run.workflow_run_id,
                ticket_id=ticket_id,
                workflow_id=selected["workflow_id"],
                customer_id=request.customer_id,
                order_id=self._extract_order_id(request.message),
            )

        return TicketResponse(
            ticket_id=ticket_id,
            workflow_run_id=workflow_run.workflow_run_id,
            selected_workflow=SelectedWorkflowResponse(
                workflow_id=selected["workflow_id"],
                name=selected["name"],
                job_type=selected["job_type"],
                confidence=selected["confidence"],
                reason=selected["reason"],
            ),
            status=ticket_status,
            requires_confirmation=requires_confirmation,
        )

    def _extract_order_id(self, message: str) -> str:
        match = re.search(r"\bO\d+\b", message, re.IGNORECASE)
        return match.group(0).upper() if match else ""


ticket_service = TicketService()
