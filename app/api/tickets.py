from fastapi import APIRouter, HTTPException, status

from app.repositories.ticket_repository import ticket_repository
from app.schemas.ticket import (
    CreateTicketRequest,
    TicketDetailResponse,
    TicketResponse,
)
from app.services.ticket_service import ticket_service


router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post(
    "",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(request: CreateTicketRequest):
    return ticket_service.create_ticket(request)


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: str):
    ticket = ticket_repository.find_by_id(ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=404,
            detail=f"Ticket not found: {ticket_id}",
        )
    return ticket
