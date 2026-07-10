from app.workflows.workflow_specs import WORKFLOW_SPECS


class WorkflowDefinitionValidator:
    def validate(self, workflow_definition) -> None:
        workflow_type = workflow_definition.workflow_type
        spec = WORKFLOW_SPECS.get(workflow_type)

        if not spec:
            raise ValueError(f"Unknown workflow_type: {workflow_type}")

        input_schema = workflow_definition.input_schema or {}
        required_fields = input_schema.get("required_fields", [])
        optional_fields = input_schema.get("optional_fields", [])

        required_field_names = [
            field.get("name")
            for field in required_fields
            if field.get("name")
        ]

        all_field_names = [
            field.get("name")
            for field in required_fields + optional_fields
            if field.get("name")
        ]

        missing_required = [
            field_name
            for field_name in spec["minimum_required_fields"]
            if field_name not in required_field_names
        ]

        if missing_required:
            raise ValueError(
                f"{workflow_type} input_schema is missing required fields: "
                f"{missing_required}"
            )

        allowed_fields = set(spec["allowed_fields"])
        invalid_fields = [
            field_name
            for field_name in all_field_names
            if field_name not in allowed_fields
        ]

        if invalid_fields:
            raise ValueError(
                f"{workflow_type} input_schema contains invalid fields: "
                f"{invalid_fields}"
            )

        if (
            workflow_definition.min_confidence < 0
            or workflow_definition.min_confidence > 1
        ):
            raise ValueError("min_confidence must be between 0 and 1")

        if not workflow_definition.description:
            raise ValueError("description is required")

        if not workflow_definition.trigger_examples:
            raise ValueError("trigger_examples cannot be empty")


workflow_definition_validator = WorkflowDefinitionValidator()
