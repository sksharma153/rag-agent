from app.embeddings.local_embedding import LocalEmbedding
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

vectorstore = ChromeVectorStore()
embedding = LocalEmbedding()
bm25retriever = BM25Retriever()

retriever = HybridRetriever(
    vectorstore= vectorstore,
    embedding=embedding,
    bm25_retriever=bm25retriever,
)

service = RetrievalService(
    hybrid_retriever=retriever,
    reranker=Reranker(),
)

results = service.retrieve(
    question="What services does he use there?",
    tenant_id="tenant_001",
    document_id="2a67845f-9e7b-4010-8fb5-11288e61a12c"
)

for chunk in results:
    print("=" * 80)
    print(chunk.score)
    print(chunk.text[:500])