from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TicketStatus(str, Enum):
    NO_MATCH = "NO_MATCH"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    PENDING = "PENDING"


class CreateTicketRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


class SelectedWorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    job_type: str
    confidence: float
    reason: str


class TicketResponse(BaseModel):
    ticket_id: str
    workflow_run_id: Optional[str]
    selected_workflow: Optional[SelectedWorkflowResponse]
    status: TicketStatus
    requires_confirmation: bool
