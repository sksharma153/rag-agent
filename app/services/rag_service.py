from app.llm.base_llm import BaseLLM
from app.model.rag_response import RagResponse, Source
from app.prompts.prompt_builder import PromptBuilder
from app.services.retrieval_service import RetrievalService

class RagService:

    def __init__(
            self,
            retrieval_service: RetrievalService,
            llm: BaseLLM
    ):
        self.retrieval_service = retrieval_service
        self.llm = llm

    def ask(
            self,
            question: str,
            tenant_id: str,
            document_id: str | None = None,
    ):

        results = self.retrieval_service.retrieve(
            question=question,
            tenant_id=tenant_id,
            document_id=document_id,
            k=5
        )

        chunks = [
            result["chunk"]
            for result in results
        ]

        prompt = PromptBuilder.build(
            question=question,
            chunks=chunks
        )

        answer = self.llm.generate(prompt)

        unique_sources = {}

        for chunk in chunks:
            document_id = chunk.metadata["document_id"]

            if document_id not in unique_sources:
                unique_sources[document_id] = {
                    "document_id": document_id,
                    "filename": chunk.metadata["filename"],
                }

        return {
            "answer": answer,
            "sources": list(unique_sources.values()),
        }