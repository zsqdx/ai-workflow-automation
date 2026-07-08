from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.schemas.workflow_run import WorkflowRunStatus


@dataclass
class WorkflowRunDefinition:
    workflow_run_id: str
    ticket_id: str
    workflow_id: str
    workflow_type: str
    customer_id: str
    input: Dict[str, Any]
    status: WorkflowRunStatus
    created_at: str
    updated_at: str
    notification_template_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
