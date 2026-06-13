from fastapi import APIRouter, status

from app.schemas.ticket import CreateTicketRequest, TicketResponse
from app.services.ticket_service import ticket_service


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(request: CreateTicketRequest):
    return ticket_service.create_ticket(request)
