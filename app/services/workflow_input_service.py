import json
import os
from typing import Optional

from openai import OpenAI

from app.workflows.workflow_specs import WORKFLOW_SPECS


class OpenAIWorkflowInputClient:
    def __init__(
        self,
        response_schema: Optional[dict] = None,
        response_name: str = "workflow_input_extraction",
    ):
        self.client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.response_schema = response_schema
        self.response_name = response_name

    def generate_json(self, prompt: str) -> dict:
        if self.client is None:
            raise RuntimeError("OPENAI_API_KEY is not set")

        response_schema = (
            self.response_schema or self._workflow_input_response_schema()
        )

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": self.response_name,
                    "strict": True,
                    "schema": response_schema,
                }
            },
        )
        return json.loads(response.output_text)

    def _workflow_input_response_schema(self) -> dict:
        field_names = sorted(
            {
                field_name
                for spec in WORKFLOW_SPECS.values()
                for field_name in spec["allowed_fields"]
            }
        )
        field_properties = {
            field_name: {
                "type": ["string", "number", "boolean", "null"]
            }
            for field_name in field_names
        }
        return {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "object",
                    "properties": field_properties,
                    "required": field_names,
                    "additionalProperties": False,
                },
                "missing_fields": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "confidence": {"type": "number"},
            },
            "required": [
                "fields",
                "missing_fields",
                "confidence",
            ],
            "additionalProperties": False,
        }


class WorkflowInputService:
    def __init__(self, llm_client: Optional[OpenAIWorkflowInputClient] = None):
        self.llm_client = llm_client or OpenAIWorkflowInputClient()

    def extract_input(
        self,
        workflow_definition,
        customer_message: str,
    ) -> dict:
        input_schema = workflow_definition.input_schema
        prompt = self._build_prompt(
            workflow_definition=workflow_definition,
            input_schema=input_schema,
            customer_message=customer_message,
        )

        raw_response = self.llm_client.generate_json(prompt)
        parsed = (
            json.loads(raw_response)
            if isinstance(raw_response, str)
            else raw_response
        )

        return {
            "fields": {
                name: value
                for name, value in parsed.get("fields", {}).items()
                if value is not None
            },
            "missing_fields": parsed.get("missing_fields", []),
            "confidence": float(parsed.get("confidence", 0.0)),
            "raw_response": parsed,
        }

    def _build_prompt(
        self,
        workflow_definition,
        input_schema: dict,
        customer_message: str,
    ) -> str:
        return f"""
You are extracting structured input for a workflow.

Workflow type: {workflow_definition.workflow_type}

Workflow description: {workflow_definition.description or ""}

Input schema:
{json.dumps(input_schema, indent=2)}

Customer message: {customer_message}

Rules:
- Extract only information explicitly present in the customer message.
- Do not guess missing values.
- Include every supported field in fields and use null when its value is not present.
- If a required field is missing, include the field name in missing_fields.
- Return JSON only.
- The JSON must use this format:
{{
  "fields": {{
    "field_name": "field_value_or_null"
  }},
  "missing_fields": [],
  "confidence": 0.0
}}
"""


workflow_input_service = WorkflowInputService()
