from app.embeddings.local_embedding import LocalEmbedding
from app.llm.ollama_llm import OllamaLLM
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.services.multi_query_generator import MultiQueryGenerator
from app.services.query_rewriter import QueryRewriter
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

embedding_service = LocalEmbedding()
vectorstore_service = ChromeVectorStore()
bm25_retriever = BM25Retriever()
reranker = Reranker()

hybrid_retriever = HybridRetriever(
    vectorstore=vectorstore_service,
    embedding=embedding_service,
    bm25_retriever=bm25_retriever,
)

retrieval_service = RetrievalService(
    hybrid_retriever=hybrid_retriever,
    reranker=reranker,
)

rag = RagService(
    retrieval_service=retrieval_service,
    llm=OllamaLLM(),
    query_rewriter=QueryRewriter(OllamaLLM()),
    multi_query_generator=MultiQueryGenerator(OllamaLLM()),
)

response = rag.ask(
    question="What is the process for making pizza?",
    tenant_id="tenant_001"
)

print(response.answer)

for source in response.sources:
    print(source.document, source.score)