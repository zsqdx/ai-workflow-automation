from dataclasses import asdict, is_dataclass

from app.workflows.workflow_specs import WORKFLOW_SPECS


class WorkflowDefinitionValidator:
    def validate(self, workflow_definition) -> None:
        workflow_definition = self._as_dict(workflow_definition)
        workflow_type = workflow_definition.get("workflow_type")
        spec = WORKFLOW_SPECS.get(workflow_type)
        if not spec:
            raise ValueError(f"Unknown workflow_type: {workflow_type}")

        input_schema = workflow_definition.get("input_schema") or {}
        required_fields = input_schema.get("required_fields") or []
        required_field_names = {
            field.get("name")
            for field in required_fields
            if field.get("name")
        }

        missing_from_definition = [
            field_name
            for field_name in spec["minimum_required_fields"]
            if field_name not in required_field_names
        ]
        if missing_from_definition:
            raise ValueError(
                f"workflow_definition for {workflow_type} is missing "
                f"required fields: {missing_from_definition}"
            )

        allowed_fields = set(spec["allowed_fields"])
        invalid_fields = [
            field_name
            for field_name in required_field_names
            if field_name not in allowed_fields
        ]
        if invalid_fields:
            raise ValueError(
                f"workflow_definition for {workflow_type} contains invalid "
                f"fields: {invalid_fields}"
            )

    def _as_dict(self, workflow_definition) -> dict:
        if is_dataclass(workflow_definition):
            return asdict(workflow_definition)
        return dict(workflow_definition)


workflow_definition_validator = WorkflowDefinitionValidator()
