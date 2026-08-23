import json

from app.embeddings.local_embedding import LocalEmbedding
from app.llm.ollama_llm import OllamaLLM

from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.vectorstore.chroma_vectorstore import ChromeVectorStore


TENANT_ID = "tenant_001"

DATASET_PATH = "eval_dataset_updated.json"
OUTPUT_PATH = "retrieval_candidates.json"


def build_retriever():

    embedding_service = LocalEmbedding()
    vectorstore_service = ChromeVectorStore()
    bm25_retriever = BM25Retriever()

    hybrid_retriever = HybridRetriever(
        vectorstore=vectorstore_service,
        embedding=embedding_service,
        bm25_retriever=bm25_retriever,
    )

    return hybrid_retriever


def main():

    hybrid_retriever = build_retriever()

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8",
    ) as file:

        dataset = json.load(file)

    output = []

    for index, item in enumerate(
        dataset,
        start=1,
    ):

        question = item["question"]
        document_id = item.get("document_id")

        print("\n" + "=" * 100)
        print(f"[{index}/{len(dataset)}] {question}")
        print("=" * 100)

        if not document_id:
            document_id = "b06a4b5e-ad90-4ed5-b297-28dd28ec9a02"
            print("Using document ID:", document_id)

        results = hybrid_retriever.retrieve(
            question=question,
            tenant_id=TENANT_ID,
            document_id=document_id,
            k=10,
        )

        print("\nDEBUG")
        print("Question:", question)
        print("Document ID:", document_id)
        print("Result type:", type(results))
        print("Result count:", len(results) if results else 0)
        print("Results:", results)
        print("DEBUG END\n")

        candidates = []

        for rank, result in enumerate(
            results,
            start=1,
        ):

            chunk = result["chunk"]

            candidate = {
                "rank": rank,
                "chunk_id": chunk.id,
                "text": chunk.text,
                "hybrid_score": result.get(
                    "hybrid_score",
                    0.0,
                ),
                "vector_score": result.get(
                    "vector_score",
                    0.0,
                ),
                "bm25_score": result.get(
                    "bm25_score",
                    0.0,
                ),
            }

            candidates.append(candidate)

            print(
                f"\nRANK {rank}"
            )

            print(
                f"CHUNK ID: {chunk.id}"
            )

            print(
                f"HYBRID SCORE: "
                f"{candidate['hybrid_score']}"
            )

            print(
                f"TEXT:\n{chunk.text[:1200]}"
            )

        output.append({
            "id": item["id"],
            "question": question,
            "expected_answer": item.get(
                "expected_answer"
            ),
            "document_id": document_id,
            "source_pages": item.get(
                "source_pages",
                []
            ),
            "candidates": candidates,

            # Fill this after reviewing candidates.
            "relevant_chunk_ids": [],
        })

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print("\n" + "=" * 100)
    print(
        f"Created candidate file: {OUTPUT_PATH}"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()