import json
import logging
import os
import re
from typing import List, Optional

from openai import OpenAI


logger = logging.getLogger(__name__)


class LLMRouterService:
    def __init__(self):
        self.client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def select_workflow(self, message: str, workflows: List) -> Optional[dict]:
        if not workflows:
            return None

        prompt = self.build_prompt(message, workflows)
        logger.info("LLM router prompt: %s", prompt)

        try:
            result = self.call_openai(prompt)
        except Exception as exc:
            logger.warning(
                "OpenAI routing failed; using mock keyword router: %s",
                exc,
            )
            result = self.call_mock_router(message, workflows)

        selected = self.validate_result(result, workflows)
        logger.info("Validated selected workflow: %s", selected)
        return selected

    def build_prompt(self, message: str, workflows: List) -> str:
        workflow_candidates = []
        for workflow in workflows:
            workflow_candidates.append(
                {
                    "workflow_id": workflow.workflow_id,
                    "name": workflow.name,
                    "description": workflow.description,
                    "job_type": workflow.job_type,
                    "workflow_type": workflow.workflow_type,
                    "requires_confirmation": workflow.requires_confirmation,
                    "min_confidence": workflow.min_confidence,
                    "trigger_examples": workflow.trigger_examples,
                }
            )

        return f"""
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
{json.dumps(workflow_candidates, indent=2)}

Customer request:
{message}
"""

    def call_openai(self, prompt: str) -> dict:
        if self.client is None:
            raise RuntimeError("OPENAI_API_KEY is not set")

        response = self.client.responses.create(
            model=self.model,
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
                                    "Selected workflow_id, or null if no "
                                    "workflow matches."
                                ),
                            },
                            "confidence": {
                                "type": "number",
                                "description": (
                                    "Confidence score between 0 and 1."
                                ),
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

        logger.info("Raw LLM response: %s", response.output_text)
        return json.loads(response.output_text)

    def call_mock_router(self, message: str, workflows: List) -> dict:
        message_tokens = self._tokenize(message)
        best_workflow = None
        best_score = 0

        for workflow in workflows:
            workflow_text = " ".join(
                [
                    workflow.name,
                    workflow.description or "",
                    workflow.job_type,
                    " ".join(workflow.trigger_examples),
                ]
            )
            workflow_tokens = self._tokenize(workflow_text)
            score = len(message_tokens.intersection(workflow_tokens))

            if score > best_score:
                best_score = score
                best_workflow = workflow

        if best_workflow is None:
            return {
                "selected_workflow_id": None,
                "confidence": 0.0,
                "reason": "No keyword match found.",
            }

        return {
            "selected_workflow_id": best_workflow.workflow_id,
            "confidence": 0.95,
            "reason": "Selected by keyword fallback router.",
        }

    def validate_result(self, result: dict, workflows: List) -> Optional[dict]:
        selected_workflow_id = result.get("selected_workflow_id")
        if selected_workflow_id is None:
            return None

        workflow_by_id = {
            workflow.workflow_id: workflow
            for workflow in workflows
        }
        if selected_workflow_id not in workflow_by_id:
            return None

        selected_workflow = workflow_by_id[selected_workflow_id]
        confidence = float(result.get("confidence", 0.0))
        if confidence < selected_workflow.min_confidence:
            return None

        return {
            "workflow_id": selected_workflow.workflow_id,
            "name": selected_workflow.name,
            "job_type": selected_workflow.job_type,
            "workflow_type": selected_workflow.workflow_type,
            "requires_confirmation": selected_workflow.requires_confirmation,
            "confidence": confidence,
            "reason": result.get("reason", ""),
        }

    def _tokenize(self, text: str) -> set:
        stop_words = {
            "and",
            "the",
            "for",
            "with",
            "that",
            "this",
            "want",
            "need",
            "issue",
            "handle",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) >= 4 and token not in stop_words
        }


llm_router_service = LLMRouterService()
