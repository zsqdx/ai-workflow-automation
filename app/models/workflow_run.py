from dataclasses import dataclass
from typing import Optional

from app.schemas.workflow_run import WorkflowRunStatus


@dataclass
class WorkflowRunDefinition:
    workflow_run_id: str
    ticket_id: str
    workflow_id: str
    job_type: str
    customer_id: str
    status: WorkflowRunStatus
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
