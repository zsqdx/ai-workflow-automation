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
        workflow_type = self._workflow_type_for(selected["job_type"])
        workflow_run_status = WorkflowRunStatus.PENDING
        if workflow_type != "REFUND_WORKFLOW" and requires_confirmation:
            workflow_run_status = WorkflowRunStatus.WAITING_FOR_CONFIRMATION

        ticket_status = TicketStatus.PENDING
        if workflow_run_status == WorkflowRunStatus.WAITING_FOR_CONFIRMATION:
            ticket_status = TicketStatus.WAITING_FOR_CONFIRMATION

        workflow_run = workflow_run_service.create_workflow_run(
            ticket_id=ticket_id,
            workflow_id=selected["workflow_id"],
            workflow_type=workflow_type,
            customer_id=request.customer_id,
            input={
                "order_id": self._extract_order_id(request.message),
                "message": request.message,
            },
            status=workflow_run_status,
        )

        if (
            workflow_run.status == WorkflowRunStatus.PENDING
            and workflow_run.workflow_type == "REFUND_WORKFLOW"
        ):
            sqs_service.send_workflow_run_message(workflow_run.workflow_run_id)

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

    def _workflow_type_for(self, job_type: str) -> str:
        if job_type == "REFUND_JOB":
            return "REFUND_WORKFLOW"
        return job_type


ticket_service = TicketService()
