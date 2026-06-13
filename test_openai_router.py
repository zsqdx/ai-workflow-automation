import json
import os

from openai import OpenAI


client = OpenAI()
model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

workflows = [
    {
        "workflow_id": "wf_refund",
        "name": "refund_workflow",
        "description": "Handle refund and return requests",
        "job_type": "REFUND_JOB",
        "requires_confirmation": True,
        "min_confidence": 0.85,
        "trigger_examples": [
            "I want a refund",
            "Can I get my money back?",
            "I want to return my order",
        ],
    },
    {
        "workflow_id": "wf_login",
        "name": "login_issue_workflow",
        "description": "Handle login, password, and account access issues",
        "job_type": "LOGIN_ISSUE_JOB",
        "requires_confirmation": False,
        "min_confidence": 0.70,
        "trigger_examples": [
            "I cannot log in",
            "I forgot my password",
            "My account is locked",
        ],
    },
]

customer_message = "I want a refund. My order number is O123."

prompt = f"""
You are a workflow routing engine.
Your job is to select the best workflow for a customer request.

Rules:
1. Only select from the provided workflows.
2. Do not invent workflow IDs.
3. If no workflow matches, return selected_workflow_id as null.
4. Return a confidence score between 0 and 1.
5. Return a short reason.
6. Return JSON only.

Available workflows:
{json.dumps(workflows, indent=2)}

Customer request:
{customer_message}
"""

response = client.responses.create(
    model=model,
    input=prompt,
    text={
        "format": {
            "type": "json_schema",
            "name": "workflow_routing_result",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "selected_workflow_id": {
                        "type": ["string", "null"],
                        "description": (
                            "Selected workflow_id, or null if no workflow "
                            "matches."
                        ),
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence score between 0 and 1.",
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "Short reason for the routing decision."
                        ),
                    },
                },
                "required": [
                    "selected_workflow_id",
                    "confidence",
                    "reason",
                ],
                "additionalProperties": False,
            },
        }
    },
)

result = json.loads(response.output_text)

print("Raw response:")
print(response.output_text)
print("\nParsed response:")
print(json.dumps(result, indent=2))
