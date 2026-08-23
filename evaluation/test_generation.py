import json

from app.embeddings.local_embedding import LocalEmbedding
from app.evaluation.generation_evaluator import GenerationEvaluator
from app.llm.ollama_llm import OllamaLLM
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.evidence_reranker import EvidenceReranker
from app.services.multi_query_generator import MultiQueryGenerator
from app.services.query_decomposer import QueryDecomposer
from app.services.query_rewriter import QueryRewriter
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

embedding_service = LocalEmbedding()
vectorstore_service = ChromeVectorStore()
bm25_retriever = BM25Retriever()
reranker = EvidenceReranker(OllamaLLM())
query_rewriter = QueryRewriter(OllamaLLM())
multi_query_generator = MultiQueryGenerator(OllamaLLM())
query_decomposer = QueryDecomposer(OllamaLLM())
judge_llm = OllamaLLM()

hybrid_retriever = HybridRetriever(
    vectorstore=vectorstore_service,
    embedding=embedding_service,
    bm25_retriever=bm25_retriever,
)

retrieval_service = RetrievalService(
    hybrid_retriever=hybrid_retriever,
    evidence_retriever=reranker,
)

rag_service = RagService(
    retrieval_service=retrieval_service,
    llm=OllamaLLM(),
    query_rewriter=query_rewriter,
    multi_query_generator=multi_query_generator,
    query_decomposer=query_decomposer,
)

def main():
    evaluator = GenerationEvaluator(
        rag_service=rag_service,
        judge_llm=judge_llm,
    )

    document_id = "c055ebfc-83dc-47ce-98d4-780d36f8cb07"
    dataset = evaluator.load_dataset("eval_database_gold.json")

    failure_report = []

    for index, item in enumerate(dataset):
        if not item["relevant_chunk_ids"]:
            print(
                f"SKIPPED [{index}/{len(dataset)}]: "
                f"{item['question']}"
            )
            continue

        result = evaluator.evaluate(
            question=item["question"],
            expected_answer=item["expected_answer"],
            tenant_id="tenant_001",
            document_id=document_id,
        )

        print("\n" + "=" * 80)
        print("GENERATION EVALUATION")
        print("=" * 80)

        print("\nQuestion:")
        print(result["question"])

        print("\nExpected Answer:")
        print(result["expected_answer"])

        print("\nAnswer:")
        print(result["answer"])

        print("\nEvaluation:")
        print(result["evaluation"])

        print("=" * 80)

        evaluation = result["evaluation"]

        correctness = evaluation.get(
            "answer_correctness"
        )

        faithfulness = evaluation.get(
            "faithfulness"
        )

        context_relevance = evaluation.get(
            "context_relevance"
        )

        if (
                context_relevance is not None
                and context_relevance < 0.8
        ):
            failure_type = "RETRIEVAL_OR_CONTEXT_FAILURE"

        elif (
                faithfulness is not None
                and faithfulness < 0.8
        ):
            failure_type = "GENERATION_OR_GROUNDING_FAILURE"

        elif (
                correctness is not None
                and correctness < 0.8
        ):
            failure_type = "GENERATION_FAILURE"

        else:
            failure_type = "PASS"

        failure_report.append({
            "id": item["id"],
            "question": item["question"],
            "expected_answer": item["expected_answer"],
            "generated_answer": result["answer"],
            "answer_correctness": correctness,
            "faithfulness": faithfulness,
            "context_relevance": context_relevance,
            "failure_type": failure_type,
            "correctness_reason": evaluation.get("correctness_reason"),
            "grounding_reason": evaluation.get("grounding_reason"),
        })

    with open(
            "generation_failure_report.json",
            "w",
            encoding="utf-8",
    ) as file:
        json.dump(
            failure_report,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "\nCreated: "
        "evaluation/generation_failure_report.json"
    )

if __name__ == "__main__":
    main()