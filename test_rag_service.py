from app.embeddings.local_embedding import LocalEmbedding
from app.llm.ollama_llm import OllamaLLM
from app.services.rag_service import RagService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

embedding_service = LocalEmbedding()
vectorstore_service = ChromeVectorStore()

retrieval_service = RetrievalService(
    embedding=embedding_service,
    vectorstore=vectorstore_service
)

rag = RagService(
    retrieval_service=retrieval_service,
    llm=OllamaLLM(),
)

response = rag.ask(
    "What is the process for making pizza?"
)

print(response.answer)

for source in response.sources:
    print(source.document, source.score)