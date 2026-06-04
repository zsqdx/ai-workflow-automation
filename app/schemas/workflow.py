from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class WorkflowStepType(str, Enum):
    LLM = "LLM"
    TOOL = "TOOL"
    RAG = "RAG"
    NOTIFICATION = "NOTIFICATION"


class WorkflowStepCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: WorkflowStepType
    tool_name: Optional[str] = None


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    trigger_examples: List[str] = Field(default_factory=list)
    steps: List[WorkflowStepCreate]


class WorkflowResponse(BaseModel):
    workflow_id: str
    name: str
    description: Optional[str]
    version: int
    status: WorkflowStatus
    trigger_examples: List[str]
    steps: List[WorkflowStepCreate]
