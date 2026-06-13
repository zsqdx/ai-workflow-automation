from dataclasses import dataclass
from typing import List, Optional

from app.schemas.workflow import WorkflowStatus


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: Optional[str]
    status: WorkflowStatus
    job_type: str
    requires_confirmation: bool
    min_confidence: float
    trigger_examples: List[str]
    version: int
