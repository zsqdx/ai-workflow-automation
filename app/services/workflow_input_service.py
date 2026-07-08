import json
import os
import re
from typing import Optional

from openai import OpenAI


class OpenAIWorkflowInputClient:
    def __init__(self):
        self.client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_json(self, prompt: str) -> dict:
        if self.client is None:
            raise RuntimeError("OPENAI_API_KEY is not set")

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "workflow_input_extraction",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "fields": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": ["string", "number", "boolean"]
                                },
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
                    },
                }
            },
        )
        return json.loads(response.output_text)


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

        try:
            raw_response = self.llm_client.generate_json(prompt)
        except Exception as exc:
            raw_response = self._extract_with_rules(
                input_schema=input_schema,
                customer_message=customer_message,
                error=str(exc),
            )

        parsed = json.loads(raw_response) if isinstance(raw_response, str) else raw_response
        return {
            "fields": parsed.get("fields", {}),
            "missing_fields": parsed.get("missing_fields", []),
            "confidence": parsed.get("confidence", 0),
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

Workflow type:
{workflow_definition.workflow_type}

Workflow description:
{workflow_definition.description or ""}

Input schema:
{json.dumps(input_schema, indent=2)}

Customer message:
{customer_message}

Rules:
- Extract only information explicitly present in the customer message.
- Do not guess missing values.
- If a required field is missing, include the field name in missing_fields.
- Return JSON only.
- The JSON must use this format:
{{
  "fields": {{
    "field_name": "field_value"
  }},
  "missing_fields": [],
  "confidence": 0.0
}}
"""

    def _extract_with_rules(
        self,
        input_schema: dict,
        customer_message: str,
        error: str,
    ) -> dict:
        fields = {}
        message = customer_message.strip()

        required_names = {
            field.get("name")
            for field in input_schema.get("required_fields", [])
        }

        if "order_id" in required_names:
            order_id = self._extract_order_id_candidate(message)
            if order_id:
                fields["order_id"] = order_id

        if "refund_reason" in required_names:
            refund_reason = self._extract_refund_reason(message)
            if refund_reason:
                fields["refund_reason"] = refund_reason

        missing_fields = [
            field["name"]
            for field in input_schema.get("required_fields", [])
            if field["name"] not in fields
        ]
        return {
            "fields": fields,
            "missing_fields": missing_fields,
            "confidence": 0.75,
            "fallback_reason": error,
        }

    def _extract_order_id_candidate(self, message: str) -> Optional[str]:
        match = re.search(
            r"\border(?:\s+(?:number|id))?\s+([A-Za-z]?\d+)\b",
            message,
            re.IGNORECASE,
        )
        if match:
            return match.group(1).upper()

        match = re.search(r"\bO\d+\b", message, re.IGNORECASE)
        if match:
            return match.group(0).upper()

        return None

    def _extract_refund_reason(self, message: str) -> Optional[str]:
        match = re.search(r"\bbecause\b(.+)$", message, re.IGNORECASE)
        if not match:
            return None

        reason = match.group(1).strip()
        return reason.rstrip(".!?") or None


workflow_input_service = WorkflowInputService()
