class RAGService:
    INSUFFICIENT_INFORMATION_ANSWER = (
        "I don't have enough information to answer that based on the current "
        "knowledge base."
    )

    def __init__(
        self,
        knowledge_base_service,
        llm_answer_service,
    ):
        self.knowledge_base_service = knowledge_base_service
        self.llm_answer_service = llm_answer_service

    def answer_question(self, question: str) -> dict:
        retrieved_documents = self.knowledge_base_service.search(
            query=question,
            top_k=3,
        )
        if not retrieved_documents:
            return {
                "question": question,
                "answer": self.INSUFFICIENT_INFORMATION_ANSWER,
                "sources": [],
            }

        answer_result = self.llm_answer_service.generate_answer(
            question=question,
            retrieved_documents=retrieved_documents,
        )

        sources = []
        used_sources = set(answer_result.get("used_sources", []))
        for document in retrieved_documents:
            if document["document_id"] in used_sources:
                sources.append(
                    {
                        "document_id": document["document_id"],
                        "title": document["title"],
                        "source_uri": document["source_uri"],
                        "score": document["score"],
                    }
                )

        return {
            "question": question,
            "answer": answer_result["answer"],
            "sources": sources,
        }
