from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class WorkflowRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"


class WorkflowRunResponse(BaseModel):
    workflow_run_id: str
    ticket_id: str
    workflow_id: str
    workflow_type: str
    customer_id: str
    notification_template_id: Optional[str] = None
    input: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    status: WorkflowRunStatus
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
