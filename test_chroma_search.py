import chromadb

from app.embeddings.local_embedding import LocalEmbedding


embedding_service = LocalEmbedding()

client = chromadb.PersistentClient(
    path="chroma_db"
)

collection = client.get_collection(
    name="documents"
)

question = "What technologies does Sandeep know?"

query_embedding = embedding_service.embed_text(
    text=question
)

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={
        "tenant_id": "tenant_001"
    },
    include=[
        "documents",
        "metadatas",
        "distances"
    ]
)

for i in range(len(results["ids"][0])):

    distance = results["distances"][0][i]

    print("=" * 80)
    print("ID:", results["ids"][0][i])
    print("Distance:", distance)
    print("Similarity:", 1 - distance)
    print("Metadata:", results["metadatas"][0][i])
    print("Text:", results["documents"][0][i][:500])