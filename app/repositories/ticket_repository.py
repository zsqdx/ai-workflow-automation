from datetime import datetime, timezone
from typing import Dict, Optional


class TicketRepository:
    def __init__(self):
        self._tickets: Dict[str, dict] = {}

    def create_ticket(
        self,
        ticket_id: str,
        customer_id: str,
        customer_email: str,
        message: str,
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "customer_email": customer_email,
            "message": message,
            "status": "CREATED",
            "created_at": now,
            "updated_at": now,
        }
        self._tickets[ticket_id] = ticket
        return ticket

    def update_status(self, ticket_id: str, status: str) -> Optional[dict]:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            return None

        ticket["status"] = status
        ticket["updated_at"] = datetime.now(timezone.utc).isoformat()
        return ticket

    def find_by_id(self, ticket_id: str) -> Optional[dict]:
        return self._tickets.get(ticket_id)


ticket_repository = TicketRepository()
