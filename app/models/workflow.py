from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.schemas.workflow import WorkflowStatus


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: Optional[str]
    status: WorkflowStatus
    job_type: str
    workflow_type: str
    requires_confirmation: bool
    min_confidence: float
    trigger_examples: List[str]
    version: int
    notification_template_id: Optional[str] = None
    input_schema: Dict[str, Any] = None

    def __post_init__(self):
        if self.input_schema is None:
            self.input_schema = {
                "required_fields": [],
                "optional_fields": [],
            }
