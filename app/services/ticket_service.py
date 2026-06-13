from uuid import uuid4

from app.schemas.ticket import (
    CreateTicketRequest,
    SelectedWorkflowResponse,
    TicketResponse,
    TicketStatus,
)
from app.services.llm_router_service import llm_router_service
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

        return TicketResponse(
            ticket_id=ticket_id,
            workflow_run_id=f"run_{uuid4()}",
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


ticket_service = TicketService()
