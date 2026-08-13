from sentence_transformers import SentenceTransformer

from app.embeddings.base_embedding import BaseEmbedding

class LocalEmbedding(BaseEmbedding):
    def __init__(self):
        self.model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5",
            device="cpu",
        )

    def embed_text(self, text):
        return self.model.encode(
            text,
            normalize_embeddings=True,
        ).tolist()

    def embed_documents(self, document):
        return self.model.encode(
            document,
            batch_size=8,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).tolist()