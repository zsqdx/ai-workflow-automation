from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    job_type: str = Field(..., min_length=1)
    workflow_type: Optional[str] = None
    requires_confirmation: bool
    min_confidence: float = Field(..., ge=0.0, le=1.0)
    trigger_examples: List[str] = Field(default_factory=list)
    notification_template_id: Optional[str] = None
    input_schema: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str]
    status: WorkflowStatus
    job_type: str
    workflow_type: str
    requires_confirmation: bool
    min_confidence: float
    trigger_examples: List[str]
    notification_template_id: Optional[str] = None
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    version: int
