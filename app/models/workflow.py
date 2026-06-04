from dataclasses import dataclass
from typing import List, Optional

from app.schemas.workflow import WorkflowStatus, WorkflowStepCreate


@dataclass
class WorkflowDefinition:
    workflow_id: str
    name: str
    description: Optional[str]
    version: int
    status: WorkflowStatus
    trigger_examples: List[str]
    steps: List[WorkflowStepCreate]
