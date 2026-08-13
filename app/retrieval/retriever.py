from app.embeddings.base_embedding import BaseEmbedding
from app.vectorstore.base_vectorstore import BaseVectorStore

class Retriever:

    def __init__(self, embedding: BaseEmbedding, vectorstore: BaseVectorStore):
        self.embedding = embedding
        self.vectorstore = vectorstore

    def retrieve(self, question: str, k: int = 5):
        query_embedding = self.embedding.embed_text(question)

        return self.vectorstore.similarity_search(
            query_embedding=query_embedding,
            k=k,
        )