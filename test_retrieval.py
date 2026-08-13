from app.embeddings.local_embedding import LocalEmbedding
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore


service = RetrievalService(
    embedding=LocalEmbedding(),
    vectorstore=ChromeVectorStore(),
)

results = service.retrieve(
    "How many rounds are there?"
)

for chunk in results:
    print("=" * 80)
    print(chunk.score)
    print(chunk.text[:500])