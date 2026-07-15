import json


RAG_ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "used_sources": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["answer", "used_sources"],
    "additionalProperties": False,
}


class LLMAnswerService:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def generate_answer(
        self,
        question: str,
        retrieved_documents: list[dict],
    ) -> dict:
        prompt = self._build_prompt(
            question=question,
            retrieved_documents=retrieved_documents,
        )
        raw_response = self.llm_client.generate_json(prompt)
        parsed = (
            json.loads(raw_response)
            if isinstance(raw_response, str)
            else raw_response
        )
        return {
            "answer": parsed.get("answer", ""),
            "used_sources": parsed.get("used_sources", []),
        }

    def _build_prompt(
        self,
        question: str,
        retrieved_documents: list[dict],
    ) -> str:
        context_blocks = []
        for document in retrieved_documents:
            context_blocks.append(
                f"""
Source ID: {document["document_id"]}
Title: {document["title"]}
Content:
{document["content"]}
"""
            )

        context = "\n---\n".join(context_blocks)
        return f"""
You are a customer support assistant.
Answer the customer's question using only the provided knowledge base context.

Customer question:
{question}

Knowledge base context:
{context}

Rules:
- Use only the provided context.
- Do not make up company policies.
- Do not answer from general knowledge.
- If the context does not contain enough information, say:
  "I don't have enough information to answer that based on the current knowledge base."
- Keep the answer clear and concise.
- Return JSON only.
- Include only provided Source IDs in used_sources.

Return this JSON format:
{{
  "answer": "...",
  "used_sources": ["source_id_1", "source_id_2"]
}}
"""
