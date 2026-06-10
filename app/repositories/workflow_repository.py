from typing import Dict, List, Optional

from app.models.workflow import WorkflowDefinition


class WorkflowRepository:
    def __init__(self):
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def save(self, workflow: WorkflowDefinition) -> WorkflowDefinition:
        self._workflows[workflow.workflow_id] = workflow
        return workflow

    def find_by_id(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def find_all(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())


workflow_repository = WorkflowRepository()
