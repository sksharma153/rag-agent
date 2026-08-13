class HybridRetriever:

    def __init__(
        self,
        vectorstore,
        embedding,
        bm25_retriever,
    ):
        self.vectorstore = vectorstore
        self.embedding = embedding
        self.bm25 = bm25_retriever

    def retrieve(
        self,
        question: str,
        tenant_id: str,
        document_id: str | None = None,
        k: int = 5,
    ):

        # -------------------------
        # Vector Search
        # -------------------------

        query_embedding = self.embedding.embed_text(
            text=question
        )

        vector_results = (
            self.vectorstore.similarity_search(
                query_embedding=query_embedding,
                k=k,
                tenant_id=tenant_id,
                document_ids=[document_id] if document_id else None,
            )
        )

        # -------------------------
        # BM25 Search
        # -------------------------

        bm25_results = self.bm25.search(
            tenant_id=tenant_id,
            document_id=document_id,
            query=question,
            k=k,
        )

        # -------------------------
        # Merge
        # -------------------------

        return self._merge_results(
            vector_results,
            bm25_results,
            k,
        )

    def _merge_results(
        self,
        vector_results,
        bm25_results,
        k,
    ):

        # --------------------------------
        # Use a dictionary for lookup only
        # --------------------------------

        merged = {}

        # --------------------------------
        # Add vector results
        # --------------------------------

        for rank, result in enumerate(
            vector_results,
            start=1
        ):

            merged[result.id] = {
                "chunk": result,
                "vector_score": result.score,
                "vector_rank": rank,
                "bm25_score": 0.0,
                "bm25_rank": None,
            }

        # --------------------------------
        # Add BM25 results
        # --------------------------------

        for rank, result in enumerate(
            bm25_results,
            start=1
        ):

            chunk = result["chunk"]

            if chunk.id in merged:

                merged[chunk.id][
                    "bm25_score"
                ] = result["score"]

                merged[chunk.id][
                    "bm25_rank"
                ] = rank

            else:

                merged[chunk.id] = {
                    "chunk": chunk,
                    "vector_score": 0.0,
                    "vector_rank": None,
                    "bm25_score": result["score"],
                    "bm25_rank": rank,
                }

        # --------------------------------
        # IMPORTANT:
        # Take a snapshot BEFORE modifying
        # --------------------------------

        merged_items = list(
            merged.values()
        )

        # --------------------------------
        # Calculate RRF
        # --------------------------------

        RRF_K = 60

        for item in merged_items:

            score = 0.0

            vector_rank = item[
                "vector_rank"
            ]

            bm25_rank = item[
                "bm25_rank"
            ]

            if vector_rank is not None:

                score += (
                    1.0 /
                    (RRF_K + vector_rank)
                )

            if bm25_rank is not None:

                score += (
                    1.0 /
                    (RRF_K + bm25_rank)
                )

            item[
                "hybrid_score"
            ] = score

        # --------------------------------
        # Sort the LIST, not dictionary
        # --------------------------------

        merged_items.sort(
            key=lambda item: item[
                "hybrid_score"
            ],
            reverse=True,
        )

        return merged_items[:k]