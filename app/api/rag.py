from fastapi import APIRouter, HTTPException

from app.schemas.rag import RAGAnswerRequest, RAGAnswerResponse
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.llm_answer_service import (
    LLMAnswerService,
    RAG_ANSWER_SCHEMA,
)
from app.services.rag_service import RAGService
from app.services.workflow_input_service import OpenAIWorkflowInputClient


router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

knowledge_base_service = KnowledgeBaseService()
llm_client = OpenAIWorkflowInputClient(
    response_schema=RAG_ANSWER_SCHEMA,
    response_name="rag_answer",
)
llm_answer_service = LLMAnswerService(llm_client=llm_client)
rag_service = RAGService(
    knowledge_base_service=knowledge_base_service,
    llm_answer_service=llm_answer_service,
)


@router.post("/answer", response_model=RAGAnswerResponse)
def answer_question(request: RAGAnswerRequest):
    try:
        return rag_service.answer_question(request.question)
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
