from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class InputFieldSchema(BaseModel):
    name: str = Field(..., min_length=1)
    type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    examples: List[str] = Field(default_factory=list)
    validation_regex: Optional[str] = None
    min_length: Optional[int] = None
    missing_field_question: Optional[str] = None


class WorkflowInputSchema(BaseModel):
    required_fields: List[InputFieldSchema] = Field(default_factory=list)
    optional_fields: List[InputFieldSchema] = Field(default_factory=list)


class CreateWorkflowRequest(BaseModel):
    name: str = Field(..., min_length=1)
    workflow_type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)

    requires_confirmation: bool = False
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    trigger_examples: List[str] = Field(default_factory=list)
    notification_template_id: Optional[str] = None
    input_schema: WorkflowInputSchema


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
    input_schema: WorkflowInputSchema = Field(default_factory=WorkflowInputSchema)
    version: int
