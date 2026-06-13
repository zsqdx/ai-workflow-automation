from typing import List

from fastapi import APIRouter, status

from app.schemas.workflow import CreateWorkflowRequest, WorkflowResponse
from app.services.workflow_service import workflow_service


router = APIRouter(prefix="/admin/workflows", tags=["workflows"])


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workflow(request: CreateWorkflowRequest):
    return workflow_service.create_workflow(request)


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
)
def get_workflow(workflow_id: str):
    return workflow_service.get_workflow(workflow_id)


@router.post(
    "/{workflow_id}/publish",
    response_model=WorkflowResponse,
)
def publish_workflow(workflow_id: str):
    return workflow_service.publish_workflow(workflow_id)


@router.get(
    "",
    response_model=List[WorkflowResponse],
)
def list_workflows():
    return workflow_service.list_workflows()
