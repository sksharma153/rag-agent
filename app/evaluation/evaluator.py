import json

from app.services.retrieval_service import RetrievalService
from app.services.query_rewriter import QueryRewriter
from app.services.multi_query_generator import MultiQueryGenerator

from app.evaluation.metrics import (
    hit_rate_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    mean_reciprocal_rank,
)


class RetrievalEvaluator:

    def __init__(
        self,
        retrieval_service: RetrievalService,
        query_rewriter: QueryRewriter,
        multi_query_generator: MultiQueryGenerator,
    ):
        self.retrieval_service = retrieval_service
        self.query_rewriter = query_rewriter
        self.multi_query_generator = multi_query_generator

    # ---------------------------------------------------------
    # Dataset
    # ---------------------------------------------------------

    def load_dataset(self, path: str):

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    # ---------------------------------------------------------
    # Extract IDs
    # ---------------------------------------------------------

    @staticmethod
    def _extract_ids(results):

        return [
            result["chunk"].id
            for result in results
        ]

    # ---------------------------------------------------------
    # Calculate metrics
    # ---------------------------------------------------------

    @staticmethod
    def _calculate_metrics(
        retrieved_ids: list[str],
        relevant_ids: set[str],
        k: int,
    ):

        return {
            "hit_rate": hit_rate_at_k(
                retrieved_ids,
                relevant_ids,
                k,
            ),
            "precision": precision_at_k(
                retrieved_ids,
                relevant_ids,
                k,
            ),
            "recall": recall_at_k(
                retrieved_ids,
                relevant_ids,
                k,
            ),
            "reciprocal_rank": reciprocal_rank(
                retrieved_ids,
                relevant_ids,
            ),
        }

    # ---------------------------------------------------------
    # 1. Hybrid only
    #
    # No reranker
    # ---------------------------------------------------------

    def hybrid_only(
        self,
        question: str,
        conversation_history: list | None = None,
        tenant_id: str = "",
        document_id: str | None = None,
        k: int = 5,
    ):

        results = self.retrieval_service.hybrid_retriever.retrieve(
            question=question,
            tenant_id=tenant_id,
            document_id=document_id,
            k=k,
        )

        return results

    # ---------------------------------------------------------
    # 2. Query Rewrite + Hybrid
    #
    # Still no reranker
    # ---------------------------------------------------------

    def query_rewrite(
        self,
        question: str,
        conversation_history: list | None,
        tenant_id: str,
        document_id: str,
        k: int,
    ):

        rewritten_query = self.query_rewriter.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        results = self.retrieval_service.hybrid_retriever.retrieve(
            question=rewritten_query,
            tenant_id=tenant_id,
            document_id=document_id,
            k=k,
        )

        return results

    # ---------------------------------------------------------
    # 3. Query Rewrite + Multi Query + Fusion
    #
    # No final reranker
    # ---------------------------------------------------------

    def multi_query(
        self,
        question: str,
        conversation_history: list | None,
        tenant_id: str,
        document_id: str,
        k: int,
    ):

        rewritten_query = self.query_rewriter.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        queries = self.multi_query_generator.generate(
            rewritten_query
        )

        # Run the existing multi-query retrieval method,
        # but temporarily bypass final reranking below by
        # implementing the fusion here.
        all_results = []

        for query in queries:

            results = (
                self.retrieval_service.hybrid_retriever.retrieve(
                    question=query,
                    tenant_id=tenant_id,
                    document_id=document_id,
                    k=10,
                )
            )

            for rank, result in enumerate(
                results,
                start=1,
            ):

                result_copy = result.copy()

                result_copy["multi_query_rank"] = rank

                all_results.append(
                    result_copy
                )

        fused_results = (
            self.retrieval_service._fuse_multi_query_results(
                all_results
            )
        )

        return fused_results[:k]

    # ---------------------------------------------------------
    # 4. Query Rewrite + Multi Query + Fusion + Reranker
    # ---------------------------------------------------------

    def multi_query_reranked(
        self,
        question: str,
        conversation_history: list | None,
        tenant_id: str,
        document_id: str,
        k: int,
    ):

        rewritten_query = self.query_rewriter.rewrite(
            question=question,
            conversation_history=conversation_history,
        )

        queries = self.multi_query_generator.generate(
            rewritten_query
        )

        return self.retrieval_service.retrieve_multi_query(
            queries=queries,
            tenant_id=tenant_id,
            document_id=document_id,
            k=k,
        )

    # ---------------------------------------------------------
    # Evaluate one configuration
    # ---------------------------------------------------------

    def evaluate_configuration(
        self,
        name: str,
        dataset: list,
        evaluator_fn,
        k: int,
    ):

        print("\n" + "=" * 90)
        print(f"CONFIGURATION: {name}")
        print("=" * 90)

        results = []
        reciprocal_ranks = []

        for index, item in enumerate(
            dataset,
            start=1,
        ):

            question = item["question"]
            document_id = item["document_id"]

            relevant_ids = set(
                item["relevant_chunk_ids"]
            )

            if not relevant_ids:
                print(
                    f"SKIPPED: {question} "
                    "(no relevant_chunk_ids yet)"
                )
                continue

            print(
                f"\n[{index}/{len(dataset)}] "
                f"{question}"
            )

            retrieved = evaluator_fn(
                question=question,
                conversation_history=[],
                tenant_id="tenant_001",
                document_id=document_id,
                k=k,
            )

            retrieved_ids = self._extract_ids(
                retrieved
            )

            metrics = self._calculate_metrics(
                retrieved_ids,
                relevant_ids,
                k,
            )

            reciprocal_ranks.append(
                metrics["reciprocal_rank"]
            )

            results.append({
                "question": question,
                **metrics,
                "retrieved_ids": retrieved_ids,
            })

            print(
                f"Hit@{k}: "
                f"{metrics['hit_rate']:.3f} | "
                f"Precision@{k}: "
                f"{metrics['precision']:.3f} | "
                f"Recall@{k}: "
                f"{metrics['recall']:.3f} | "
                f"RR: "
                f"{metrics['reciprocal_rank']:.3f}"
            )

        return {
            "configuration": name,
            "questions": len(results),
            "hit_rate": (
                sum(
                    r["hit_rate"]
                    for r in results
                )
                / len(results)
            ),
            "precision": (
                sum(
                    r["precision"]
                    for r in results
                )
                / len(results)
            ),
            "recall": (
                sum(
                    r["recall"]
                    for r in results
                )
                / len(results)
            ),
            "mrr": mean_reciprocal_rank(
                reciprocal_ranks
            ),
            "results": results,
        }

    # ---------------------------------------------------------
    # Evaluate all configurations
    # ---------------------------------------------------------

    def evaluate_all(
        self,
        dataset: list,
        k: int = 5,
    ):

        evaluations = []

        configurations = [
            (
                "Hybrid Only",
                self.hybrid_only,
            ),
            (
                "Query Rewrite + Hybrid",
                self.query_rewrite,
            ),
            (
                "Multi-Query + Fusion",
                self.multi_query,
            ),
            (
                "Multi-Query + Fusion + Reranker",
                self.multi_query_reranked,
            ),
        ]

        for name, fn in configurations:

            report = self.evaluate_configuration(
                name=name,
                dataset=dataset,
                evaluator_fn=fn,
                k=k,
            )

            evaluations.append(report)

        return evaluations

    # ---------------------------------------------------------
    # Print comparison
    # ---------------------------------------------------------

    @staticmethod
    def print_comparison(
        evaluations: list,
        k: int,
    ):

        print("\n")
        print("=" * 95)
        print("RAG EVALUATION COMPARISON")
        print("=" * 95)

        print(
            f"{'Configuration':<38}"
            f"{'Hit@' + str(k):<10}"
            f"{'Precision':<12}"
            f"{'Recall':<10}"
            f"{'MRR':<10}"
        )

        print("-" * 95)

        for report in evaluations:

            print(
                f"{report['configuration']:<38}"
                f"{report['hit_rate']:<10.3f}"
                f"{report['precision']:<12.3f}"
                f"{report['recall']:<10.3f}"
                f"{report['mrr']:<10.3f}"
            )

        print("=" * 95)