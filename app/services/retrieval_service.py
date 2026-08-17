class RetrievalService:

    def __init__(
            self,
            hybrid_retriever,
            reranker
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker

    def retrieve(
            self,
            question: str,
            tenant_id: str,
            document_id: str | None = None,
            k: int = 3,
    ):

        # Get the larger candidate set first
        candidates = self.hybrid_retriever.retrieve(question, tenant_id, document_id, k=10)

        # Rerank the candidates
        results = self.reranker.rerank(question, candidates, k=k)

        return results

    def retrieve_multi_query(
            self,
            queries: list[str],
            tenant_id: str,
            document_id: str | None = None,
            k: int = 3,
    ):
        all_results = []

        for index, query in enumerate(queries):

            results = self.hybrid_retriever.retrieve(
                question=query,
                tenant_id=tenant_id,
                document_id=document_id,
                k=10
            )

            for rank, result in enumerate(results, start=1):
                result_copy = result.copy()
                result_copy["query_index"] = index
                result_copy["multi_query_rank"] = rank
                all_results.append(result_copy)

        fused_results = self._fuse_multi_query_results(all_results)

        results = self.reranker.rerank(
            queries[0],
            fused_results,
            k
        )

        return results


    def _deduplicate_results(
            self,
            results,
    ):
        unique_results = {}
        for result in results:
            chunk = result["chunk"]
            result_id = chunk.id

            if result_id not in unique_results:
                unique_results[result_id] = result

        return list(unique_results.values())

    def _fuse_multi_query_results(self, results):

        grouped = {}
        RRF_K = 60
        for result in results:

            if not isinstance(result, dict):
                continue
            chunk = result.get("chunk")

            if chunk is None:
                continue
            chunk_id = chunk.id
            rank = result.get("multi_query_rank")

            if rank is None:
                continue
            if chunk_id not in grouped:
                grouped[chunk_id] = {
                    "chunk": chunk,
                    "query_hits": 0,
                    "fusion_score": 0.0,
                }
            grouped[chunk_id]["query_hits"] += 1
            grouped[chunk_id]["fusion_score"] += (
                    1.0 / (RRF_K + rank)
            )
        fused_results = list(grouped.values())
        fused_results.sort(
            key=lambda x: x["fusion_score"],
            reverse=True,
        )
        return fused_results

    def retrieve_decomposed(
            self,
            sub_questions: list[str],
            tenant_id: str,
            document_id: str | None = None,
            k: int = 3,
    ):

        decomposed_results = []

        for index, sub_question in enumerate(sub_questions):

            results = self.retrieve(
                question=sub_question,
                tenant_id=tenant_id,
                document_id=document_id,
                k=k
            )

            decomposed_results.append({
                "sub_question": sub_question,
                "results": results
            })

        return decomposed_results