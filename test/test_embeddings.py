from app.embeddings.local_embedding import LocalEmbedding

embedding_service = LocalEmbedding()

vector = embedding_service.embed_text(
    "What is Google Cloud Storage?"
)

print(type(vector))
print(len(vector))

print(vector[:10])