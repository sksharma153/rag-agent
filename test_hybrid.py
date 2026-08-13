from app.embeddings.local_embedding import LocalEmbedding
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

vectorstore = ChromeVectorStore()
embedding = LocalEmbedding()
bm25retriever = BM25Retriever()

retriever = HybridRetriever(
    vectorstore= vectorstore,
    embedding=embedding,
    bm25_retriever=bm25retriever,
)

results = retriever.retrieve(
    question="How many years of experience?",
    tenant_id="tenant_001",
    k=5
)

for result in results:

    print("=" * 80)

    print("ID:", result["chunk"].id)

    print("Vector score:", result["vector_score"])

    print("Vector rank:", result["vector_rank"])

    print("BM25 score:", result["bm25_score"])

    print("BM25 rank:", result["bm25_rank"])

    print("RRF score:", result["hybrid_score"])

    print(
        "Text:",
        result["chunk"].text[:500]
    )