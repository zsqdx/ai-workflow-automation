from fastapi import APIRouter

from app.schemas.workflow_run import WorkflowRunResponse
from app.services.workflow_run_service import workflow_run_service


router = APIRouter(prefix="/workflow-runs", tags=["workflow-runs"])


@router.get("/{workflow_run_id}", response_model=WorkflowRunResponse)
def get_workflow_run(workflow_run_id: str):
    workflow_run = workflow_run_service.get_workflow_run(workflow_run_id)
    return WorkflowRunResponse(
        workflow_run_id=workflow_run.workflow_run_id,
        ticket_id=workflow_run.ticket_id,
        workflow_id=workflow_run.workflow_id,
        workflow_type=workflow_run.workflow_type,
        customer_id=workflow_run.customer_id,
        notification_template_id=workflow_run.notification_template_id,
        input=workflow_run.input,
        result=workflow_run.result,
        status=workflow_run.status,
        created_at=workflow_run.created_at,
        updated_at=workflow_run.updated_at,
        started_at=workflow_run.started_at,
        completed_at=workflow_run.completed_at,
        error_message=workflow_run.error_message,
    )
