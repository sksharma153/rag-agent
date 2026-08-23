from app.embeddings.local_embedding import LocalEmbedding
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.vectorstore.chroma_vectorstore import ChromeVectorStore


DOCUMENT_ID = "d6e44b72-31b9-4385-b486-ded186e7707e"
TENANT_ID = "tenant_001"


embedding = LocalEmbedding()
vectorstore = ChromeVectorStore()
bm25 = BM25Retriever()

retriever = HybridRetriever(
    vectorstore=vectorstore,
    embedding=embedding,
    bm25_retriever=bm25,
)


question = "What is the policy number?"

results = retriever.retrieve(
    question=question,
    tenant_id=TENANT_ID,
    document_id=DOCUMENT_ID,
    k=5,
)

print("\nRESULT COUNT:", len(results))

for index, result in enumerate(results, start=1):

    print("\n" + "=" * 80)
    print("RESULT:", index)

    child = result.get("child")
    parent = result.get("parent")

    print("CHILD ID:", child.id if child else None)

    if child:
        print(
            "PARENT ID:",
            child.metadata.get("parent_id"),
        )

        print(
            "CHILD TYPE:",
            child.metadata.get("chunk_type"),
        )

        print(
            "CHILD TEXT:",
            child.text[:1000] if child else None
        )

    print(
        "PARENT FOUND:",
        parent is not None,
    )

    if parent:
        print(
            "PARENT ID:",
            parent.id,
        )

        print(
            "PARENT HEADING:",
            parent.metadata.get("heading"),
        )

        print(
            "PARENT TEXT:",
            parent.text[:1000],
        )

    print(
        "HYBRID SCORE:",
        result.get("hybrid_score"),
    )

    print("=" * 80)