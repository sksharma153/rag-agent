from app.llm.base_llm import BaseLLM
from app.prompts.prompt_builder import PromptBuilder
from app.prompts.decomposition_prompt import build_decomposition_context

from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_service import RetrievalService
from app.services.multi_query_generator import MultiQueryGenerator
from app.services.query_decomposer import QueryDecomposer


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
        # Default values
        if conversation_history is None:
            conversation_history = []

        context = ""
        final_chunks = []
        unique_scores = {}

        # 1. QUERY REWRITE
        rewritten_query = self.query_rewriter.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        # 2. QUERY DECOMPOSITION
        sub_questions = self.query_decomposer.decompose(
            question=rewritten_query,
            conversation_history=conversation_history,
        )

        if len(sub_questions) <= 1:

            """queries = (
                self.multi_query_generator.generate(
                    rewritten_query
                )
            )"""

            # Retrieve
            results = (
                self.retrieval_service
                .retrieve(
                    question=question,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    k=5,
                )
            )

            # Extract chunks
            final_chunks = self._build_context_chunks(results)

            # Build context
            context = "\n\n".join(
                chunk.text
                for chunk in final_chunks
            )

            # Build prompt
            prompt = PromptBuilder.build(
                question=question,
                chunks=final_chunks,
            )

            answer = self.llm.generate(
                prompt
            )

            # Sources
            unique_scores = (
                self._build_sources(
                    final_chunks
                )
            )

        else:
            decomposed_results = (
                self.retrieval_service
                .retrieve_decomposed(
                    sub_questions=sub_questions,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    k=5,
                )
            )

            # Group evidence
            decomposed_context = []
            for item in decomposed_results:
                sub_question = item[
                    "sub_question"
                ]
                sub_chunks = self._build_context_chunks(item["results"])
                decomposed_context.append(
                    {
                        "sub_question": sub_question,
                        "chunks": sub_chunks,
                    }
                )

            # Flatten chunks for source tracking
            final_chunks = []
            for item in decomposed_context:
                final_chunks.extend(
                    item["chunks"]
                )

            # Build context
            context_parts = []
            for item in decomposed_context:
                context_parts.append(
                    f"SUB-QUESTION:\n"
                    f"{item['sub_question']}"
                )
                context_parts.append(
                    "EVIDENCE:\n"
                    + "\n\n".join(
                        chunk.text
                        for chunk in item["chunks"]
                    )
                )
            context = "\n\n".join(
                context_parts
            )

            # Build decomposition prompt
            prompt = build_decomposition_context(
                original_question=question,
                decomposed_context=decomposed_context,
            )

            # Generate answer
            answer = self.llm.generate(
                prompt
            )

            # Sources
            unique_scores = (
                self._build_sources(
                    final_chunks
                )
            )

        # 5. RESPONSE
        return {
            "answer": answer,
            "sources": list(unique_scores.values()),
            "context": context,
        }

    # =========================================================
    # SOURCE BUILDER
    # =========================================================

    def _build_sources(
        self,
        chunks: list,
    ):
        unique_sources = {}
        for chunk in chunks:
            chunk_document_id = (
                chunk.metadata.get(
                    "document_id"
                )
            )
            filename = (
                chunk.metadata.get(
                    "filename"
                )
            )
            if chunk_document_id not in unique_sources:
                unique_sources[
                    chunk_document_id
                ] = {
                    "document_id":
                        chunk_document_id,
                    "filename":
                        filename,
                }

        return unique_sources

    def _build_context_chunks(
            self,
            results,
            max_results: int = 5,
    ):
        """
        Convert reranked retrieval results into the
        chunks that will be sent to the LLM.
        Retrieval result structure:
            {
                "chunk": DocumentChunk,
                "rerank_score": ...,
                ...
            }
        We deliberately use result["chunk"] here.
        """

        chunks = []
        seen_ids = set()
        for result in results:
            chunk = result.get("chunk")
            if chunk is None:
                continue
            if chunk.id in seen_ids:
                continue
            seen_ids.add(chunk.id)
            chunks.append(chunk)
            if len(chunks) >= max_results:
                break
        return chunks