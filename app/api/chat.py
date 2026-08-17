from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_current_tenant
from app.embeddings.local_embedding import LocalEmbedding
from app.llm.ollama_llm import OllamaLLM
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.services.multi_query_generator import MultiQueryGenerator
from app.services.query_decomposer import QueryDecomposer
from app.services.query_rewriter import QueryRewriter
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

class ConversationMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    document_id: str | None = None
    conversation_history: list[ConversationMessage] = Field(default_factory=list)

embedding_service = LocalEmbedding()
vectorstore_service = ChromeVectorStore()
bm25_retriever = BM25Retriever()
reranker = Reranker()
query_rewriter = QueryRewriter(OllamaLLM())
multi_query_generator = MultiQueryGenerator(OllamaLLM())
query_decomposer = QueryDecomposer(OllamaLLM())

hybrid_retriever = HybridRetriever(
    vectorstore=vectorstore_service,
    embedding=embedding_service,
    bm25_retriever=bm25_retriever,
)

retrieval_service = RetrievalService(
    hybrid_retriever=hybrid_retriever,
    reranker=reranker,
)

rag_service = RagService(
    retrieval_service=retrieval_service,
    llm=OllamaLLM(),
    query_rewriter=query_rewriter,
    multi_query_generator=multi_query_generator,
    query_decomposer=query_decomposer,

)

@router.post("")
def chat(
        request: ChatRequest,
        tenant_id: str = Depends(get_current_tenant)
):

    return rag_service.ask(
        question = request.question,
        tenant_id=tenant_id,
        document_id=request.document_id,
        conversation_history=[
            message.model_dump()
            for message in request.conversation_history
        ]
    )


