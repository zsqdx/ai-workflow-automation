from typing import Dict, Optional

from app.models.workflow_run import WorkflowRunDefinition


class WorkflowRunRepository:
    def __init__(self):
        self._workflow_runs: Dict[str, WorkflowRunDefinition] = {}

    def save(self, workflow_run: WorkflowRunDefinition) -> WorkflowRunDefinition:
        self._workflow_runs[workflow_run.workflow_run_id] = workflow_run
        return workflow_run

    def find_by_id(self, workflow_run_id: str) -> Optional[WorkflowRunDefinition]:
        return self._workflow_runs.get(workflow_run_id)


workflow_run_repository = WorkflowRunRepository()
