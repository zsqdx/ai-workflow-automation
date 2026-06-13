from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    job_type: str = Field(..., min_length=1)
    requires_confirmation: bool
    min_confidence: float = Field(..., ge=0.0, le=1.0)
    trigger_examples: List[str] = Field(default_factory=list)


class WorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str]
    status: WorkflowStatus
    job_type: str
    requires_confirmation: bool
    min_confidence: float
    trigger_examples: List[str]
    version: int
