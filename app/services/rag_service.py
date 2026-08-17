from typer import prompt

from app.llm.base_llm import BaseLLM
from app.prompts.prompt_builder import PromptBuilder
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_service import RetrievalService
from app.services.multi_query_generator import MultiQueryGenerator
from app.services.query_decomposer import QueryDecomposer
from app.prompts.decomposition_prompt import build_decomposition_context

class RagService:

    def __init__(
            self,
            retrieval_service: RetrievalService,
            llm: BaseLLM,
            query_rewriter: QueryRewriter,
            multi_query_generator: MultiQueryGenerator,
            query_decomposer: QueryDecomposer,
    ):
        self.retrieval_service = retrieval_service
        self.llm = llm
        self.query_rewriter = query_rewriter
        self.multi_query_generator = multi_query_generator
        self.query_decomposer = query_decomposer

    def ask(
            self,
            question: str,
            tenant_id: str,
            document_id: str | None = None,
            conversation_history: list | None = None,
    ):

        # 1. Rewrite query
        rewritten_query = self.query_rewriter.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        sub_questions = self.query_decomposer.decompose(
            question=rewritten_query,
            conversation_history=conversation_history,
        )

        if len(sub_questions) == 1:

            # Generate multiple search queries
            queries = self.multi_query_generator.generate(
                rewritten_query,
            )

            # 2. Retrieve using rewritten query
            results = self.retrieval_service.retrieve_multi_query(
                queries=queries,
                tenant_id=tenant_id,
                document_id=document_id,
                k=5
            )

            # Extract Chunks
            chunks = [
                result["chunk"]
                for result in results
            ]

            # Build Prompt
            prompt = PromptBuilder.build(
                question=question,
                chunks=chunks
            )

            # Generate answer
            answer = self.llm.generate(prompt)
            unique_scores = self._build_sources(chunks)

        else:
            #complex Question
            decomposed_results = (
                self.retrieval_service.retrieve_decomposed(
                    sub_questions=sub_questions,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    k=5
                )
            )

            decomposed_context = []

            for item in decomposed_results:
                sub_question = item["sub_question"]

                sub_chuks = [
                    result["chunk"]
                    for result in item["results"]
                ]

                decomposed_context.append({
                    "sub_question": sub_question,
                    "chunks": sub_chuks,
                })

            prompt = build_decomposition_context(
                original_question=question,
                decomposed_context=decomposed_context,
            )

            answer = self.llm.generate(prompt)
            all_chunks = []
            for item in decomposed_context:
                all_chunks.extend(item["chunks"])

            unique_scores = self._build_sources(all_chunks)

        return {
            "answer": answer,
            "sources": list(
                unique_scores.values()
            )
        }

    def _build_sources(
            self,
            chunks: list
    ):
        unique_sources = {}

        for chunk in chunks:
            document_id = chunk.metadata["document_id"]

            if document_id not in unique_sources:
                unique_sources[document_id] = {
                    "document_id": document_id,
                    "filename": chunk.metadata["filename"],
                }

        return unique_sources