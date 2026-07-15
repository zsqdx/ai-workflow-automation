from typing import List

from pydantic import BaseModel, Field


class RAGAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1)


class RAGSource(BaseModel):
    document_id: str
    title: str
    source_uri: str
    score: int


class RAGAnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[RAGSource]
