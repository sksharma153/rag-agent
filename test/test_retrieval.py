from app.embeddings.local_embedding import LocalEmbedding
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore


TENANT_ID = "tenant_001"

DOCUMENT_ID = (
    "c055ebfc-83dc-47ce-98d4-780d36f8cb07"
)

QUESTION = "What is the maturity date?"


def print_separator(title: str):
    print("\n")
    print("=" * 100)
    print(title)
    print("=" * 100)


def print_chunk(rank: int, chunk):
    print(f"{rank:02d}. {chunk.id}")

    print(
        chunk.text[:500]
        .replace("\n", " ")
    )

    print("-" * 100)


def main():

    # ---------------------------------------------------------
    # Services
    # ---------------------------------------------------------

    embedding_service = LocalEmbedding()

    vectorstore = ChromeVectorStore()

    bm25_retriever = BM25Retriever()

    hybrid_retriever = HybridRetriever(
        vectorstore=vectorstore,
        embedding=embedding_service,
        bm25_retriever=bm25_retriever,
    )

    reranker = Reranker()

    retrieval_service = RetrievalService(
        hybrid_retriever=hybrid_retriever,
        reranker=reranker,
    )

    # ---------------------------------------------------------
    # Basic information
    # ---------------------------------------------------------

    print_separator("RETRIEVER DEBUG")

    print("TENANT:")
    print(TENANT_ID)

    print("\nDOCUMENT:")
    print(DOCUMENT_ID)

    # ---------------------------------------------------------
    # Document check
    # ---------------------------------------------------------

    print_separator("DOCUMENT CHECK")

    try:
        documents = vectorstore.list_documents()

        print("Documents:")

        for document in documents:
            print(document)

    except Exception as exc:
        print(
            "Error listing documents:",
            exc
        )

    # ---------------------------------------------------------
    # BM25 check
    # ---------------------------------------------------------

    print_separator("BM25 CHECK")

    try:
        print(
            "BM25 tenants:",
            list(
                bm25_retriever.tenant_indexes.keys()
            )
        )

    except Exception as exc:
        print(
            "Error checking BM25:",
            exc
        )

    # ---------------------------------------------------------
    # VECTOR SEARCH
    # ---------------------------------------------------------

    print_separator(
        f"VECTOR SEARCH: {QUESTION}"
    )

    try:

        query_embedding = (
            embedding_service.embed_text(
                QUESTION
            )
        )

        vector_results = (
            vectorstore.similarity_search(
                query_embedding=query_embedding,
                k=30,
                tenant_id=TENANT_ID,
                document_ids=[DOCUMENT_ID],
            )
        )

        print(
            "VECTOR RESULT COUNT:",
            len(vector_results)
        )

        for rank, chunk in enumerate(
            vector_results,
            start=1,
        ):

            print_chunk(
                rank,
                chunk
            )

    except Exception as exc:

        print(
            "VECTOR SEARCH ERROR:",
            type(exc).__name__,
            exc
        )

        vector_results = []

    # ---------------------------------------------------------
    # BM25 SEARCH
    # ---------------------------------------------------------

    print_separator(
        f"BM25 SEARCH: {QUESTION}"
    )

    try:

        bm25_results = (
            bm25_retriever.search(
                tenant_id=TENANT_ID,
                document_id=DOCUMENT_ID,
                query=QUESTION,
                k=30,
            )
        )

        print(
            "BM25 RESULT COUNT:",
            len(bm25_results)
        )

        for rank, result in enumerate(
            bm25_results,
            start=1,
        ):

            chunk = result["chunk"]

            print(
                f"{rank:02d}. "
                f"{chunk.id} "
                f"score={result.get('score')}"
            )

            print(
                chunk.text[:500]
                .replace("\n", " ")
            )

            print(
                "-" * 100
            )

    except Exception as exc:

        print(
            "BM25 SEARCH ERROR:",
            type(exc).__name__,
            exc
        )

        bm25_results = []

    # ---------------------------------------------------------
    # HYBRID SEARCH
    # ---------------------------------------------------------

    print_separator(
        f"HYBRID SEARCH: {QUESTION}"
    )

    try:

        hybrid_results = (
            hybrid_retriever.retrieve(
                question=QUESTION,
                tenant_id=TENANT_ID,
                document_id=DOCUMENT_ID,
                k=30,
            )
        )

        print(
            "HYBRID RESULT COUNT:",
            len(hybrid_results)
        )

        for rank, result in enumerate(
            hybrid_results,
            start=1,
        ):

            chunk = result["chunk"]

            print(
                f"{rank:02d}. "
                f"{chunk.id} "
                f"hybrid="
                f"{result.get('hybrid_score')} "
                f"vector="
                f"{result.get('vector_score')} "
                f"bm25="
                f"{result.get('bm25_score')}"
            )

            print(
                chunk.text[:500]
                .replace("\n", " ")
            )

            print(
                "-" * 100
            )

    except Exception as exc:

        print(
            "HYBRID SEARCH ERROR:",
            type(exc).__name__,
            exc
        )

        hybrid_results = []

    # ---------------------------------------------------------
    # RERANKING
    # ---------------------------------------------------------

    print_separator(
        f"RERANKING: {QUESTION}"
    )

    try:

        reranked_results = (
            reranker.rerank(
                question=QUESTION,
                results=hybrid_results,
                k=5,
            )
        )

        print(
            "RERANKED RESULT COUNT:",
            len(reranked_results)
        )

        for rank, result in enumerate(
            reranked_results,
            start=1,
        ):

            chunk = result["chunk"]

            print(
                f"{rank:02d}. "
                f"{chunk.id} "
                f"rerank="
                f"{result.get('rerank_score')}"
            )

            print(
                chunk.text[:500]
                .replace("\n", " ")
            )

            print(
                "-" * 100
            )

    except Exception as exc:

        print(
            "RERANK ERROR:",
            type(exc).__name__,
            exc
        )

        reranked_results = []

    # ---------------------------------------------------------
    # RETRIEVAL SERVICE
    # ---------------------------------------------------------

    print_separator(
        f"RETRIEVAL SERVICE: {QUESTION}"
    )

    try:

        retrieval_results = (
            retrieval_service.retrieve(
                question=QUESTION,
                tenant_id=TENANT_ID,
                document_id=DOCUMENT_ID,
                k=5,
            )
        )

        print(
            "RETRIEVAL SERVICE RESULT COUNT:",
            len(retrieval_results)
        )

        for rank, result in enumerate(
            retrieval_results,
            start=1,
        ):

            chunk = result["chunk"]

            print(
                f"{rank:02d}. "
                f"{chunk.id} "
                f"rerank="
                f"{result.get('rerank_score')}"
            )

            print(
                chunk.text[:500]
                .replace("\n", " ")
            )

            print(
                "-" * 100
            )

    except Exception as exc:

        print(
            "RETRIEVAL SERVICE ERROR:",
            type(exc).__name__,
            exc
        )

        retrieval_results = []

    # ---------------------------------------------------------
    # P6 SEARCH
    # ---------------------------------------------------------

    print_separator(
        "SEARCH FOR POLICY DETAILS CHUNKS"
    )

    all_stages = {
        "VECTOR": vector_results,
        "HYBRID": [
            result["chunk"]
            for result in hybrid_results
        ],
        "RERANKED": [
            result["chunk"]
            for result in reranked_results
        ],
        "RETRIEVAL SERVICE": [
            result["chunk"]
            for result in retrieval_results
        ],
    }

    # BM25 chunks are dictionaries
    all_stages["BM25"] = [
        result["chunk"]
        for result in bm25_results
    ]

    for stage_name, chunks in all_stages.items():

        matching = [
            chunk
            for chunk in chunks
            if ":P6:" in chunk.id
        ]

        print(
            f"\n{stage_name}: "
            f"{len(matching)} P6 chunks found"
        )

        for chunk in matching:

            print(
                "  ",
                chunk.id
            )

            print(
                "  ",
                chunk.text[:1000]
                .replace("\n", " ")
            )

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    print_separator("DIAGNOSTIC SUMMARY")

    print(
        "Vector results:",
        len(vector_results)
    )

    print(
        "BM25 results:",
        len(bm25_results)
    )

    print(
        "Hybrid results:",
        len(hybrid_results)
    )

    print(
        "Reranked results:",
        len(reranked_results)
    )

    print(
        "RetrievalService results:",
        len(retrieval_results)
    )

    print("\nP6 presence:")

    for stage_name, chunks in all_stages.items():

        found = any(
            ":P6:" in chunk.id
            for chunk in chunks
        )

        print(
            f"{stage_name:20s}:",
            "FOUND" if found else "NOT FOUND"
        )


if __name__ == "__main__":
    main()