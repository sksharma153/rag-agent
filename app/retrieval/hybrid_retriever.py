from __future__ import annotations

from typing import Any


class HybridRetriever:
    """
    Generic hybrid retriever.
    Retrieval flow:
        Vector Search
             +
        BM25 Search
             ↓
        Score Normalization
             ↓
        Score-Aware Fusion
             ↓
        Top-K Candidates
             ↓
        Parent Expansion
    """

    def __init__(
        self,
        vectorstore,
        embedding,
        bm25_retriever,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
    ):
        self.vectorstore = vectorstore
        self.embedding = embedding
        self.bm25_retriever = bm25_retriever

        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight

    def retrieve(
        self,
        question: str,
        tenant_id: str,
        document_id: str | None = None,
        k: int = 10,
    ) -> list[dict[str, Any]]:

        # -----------------------------------------------------
        # 1. Vector search
        # -----------------------------------------------------

        query_embedding = self.embedding.embed_text(
            question
        )

        vector_results = (
            self.vectorstore.similarity_search(
                query_embedding=query_embedding,
                k=k,
                tenant_id=tenant_id,
                document_ids=(
                    [document_id]
                    if document_id
                    else None
                ),
            )
        )

        # -----------------------------------------------------
        # 2. BM25 search
        # -----------------------------------------------------

        bm25_results = self.bm25_retriever.search(
            tenant_id=tenant_id,
            document_id=document_id,
            query=question,
            k=k,
        )

        # -----------------------------------------------------
        # 3. Normalize scores
        # -----------------------------------------------------

        vector_scores = [
            self._extract_vector_score(
                result,
                index,
                vector_results,
            )
            for index, result in enumerate(
                vector_results
            )
        ]

        bm25_scores = [
            self._extract_bm25_score(
                result,
            )
            for result in bm25_results
        ]

        normalized_vector_scores = (
            self._min_max_normalize(
                vector_scores
            )
        )

        normalized_bm25_scores = (
            self._min_max_normalize(
                bm25_scores
            )
        )

        # -----------------------------------------------------
        # 4. Merge candidates by chunk ID
        # -----------------------------------------------------

        merged: dict[str, dict[str, Any]] = {}

        # -------------------------
        # Vector candidates
        # -------------------------

        for index, result in enumerate(
            vector_results
        ):

            chunk = self._extract_vector_chunk(
                result
            )

            if chunk is None:
                continue

            chunk_id = chunk.id

            item = merged.setdefault(
                chunk_id,
                {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "bm25_score": 0.0,
                    "vector_rank": None,
                    "bm25_rank": None,
                },
            )

            item["vector_score"] = (
                normalized_vector_scores[index]
            )

            item["vector_rank"] = index + 1

        # BM25 candidates

        for index, result in enumerate(
            bm25_results
        ):

            chunk = self._extract_bm25_chunk(
                result
            )

            if chunk is None:
                continue

            chunk_id = chunk.id

            item = merged.setdefault(
                chunk_id,
                {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "bm25_score": 0.0,
                    "vector_rank": None,
                    "bm25_rank": None,
                },
            )

            item["bm25_score"] = (
                normalized_bm25_scores[index]
            )

            item["bm25_rank"] = index + 1

        # 5. Score-aware fusion
        fused_results = []

        for item in merged.values():

            vector_score = item[
                "vector_score"
            ]

            bm25_score = item[
                "bm25_score"
            ]

            hybrid_score = (
                self.vector_weight * vector_score
                + self.bm25_weight * bm25_score
            )

            fused_results.append(
                {
                    "chunk": item["chunk"],
                    "hybrid_score": hybrid_score,
                    "vector_score": vector_score,
                    "bm25_score": bm25_score,
                    "vector_rank": item["vector_rank"],
                    "bm25_rank": item["bm25_rank"],
                }
            )

        # 6. Sort by hybrid score
        fused_results.sort(
            key=lambda result: result[
                "hybrid_score"
            ],
            reverse=True,
        )

        return fused_results

    # Score helpers
    @staticmethod
    def _min_max_normalize(
        scores: list[float],
    ) -> list[float]:

        if not scores:
            return []

        minimum = min(scores)
        maximum = max(scores)

        if maximum == minimum:
            return [
                1.0
                for _ in scores
            ]

        return [
            (score - minimum)
            / (maximum - minimum)
            for score in scores
        ]

    @staticmethod
    def _extract_vector_chunk(
        result,
    ):

        # DocumentChunk directly
        if hasattr(result, "id"):
            return result

        # dict-based result
        if isinstance(result, dict):
            return result.get("chunk")

        return None

    @staticmethod
    def _extract_bm25_chunk(
        result,
    ):

        if isinstance(result, dict):
            return result.get("chunk")

        if hasattr(result, "id"):
            return result

        return None

    @staticmethod
    def _extract_vector_score(
        result,
        index: int,
        results: list,
    ) -> float:

        if isinstance(result, dict):

            score = result.get("score")

            if score is not None:
                return float(score)

        # Chroma result may not expose a score directly.
        # Preserve ranking information as a fallback.
        return 1.0 / (index + 1)

    @staticmethod
    def _extract_bm25_score(
        result,
    ) -> float:

        if isinstance(result, dict):

            score = result.get("score")

            if score is not None:
                return float(score)

        return 0.0

    def get_parent(self, parent_id: int) :
        return self.vectorstore.get_parents(parent_id)