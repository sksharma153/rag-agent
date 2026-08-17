from app.retrieval.bm25_retriever import BM25Retriever

bm25 = BM25Retriever()

results = bm25.search(
    tenant_id="tenant_001",
    query="How many years of experience?",
    k=5
)

print("RESULT COUNT", len(results))

for result in results:
    print("=" * 80)

    print("ID:", result["chunk"].id)

    print(
        "Score:",
        result["score"]
    )

    print(
        "Text:",
        result["chunk"].text[:300]
    )