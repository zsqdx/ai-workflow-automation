from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class TicketStatus(str, Enum):
    CREATED = "CREATED"
    NO_MATCH = "NO_MATCH"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    PENDING = "PENDING"
    NEEDS_MORE_INFO = "NEEDS_MORE_INFO"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    WORKFLOW_STARTED = "WORKFLOW_STARTED"


class CreateTicketRequest(BaseModel):
    customer_id: str = Field(..., min_length=1)
    customer_email: EmailStr
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
    workflow_id: Optional[str] = None
    workflow_type: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    validation_errors: List[dict] = Field(default_factory=list)
    message: Optional[str] = None
