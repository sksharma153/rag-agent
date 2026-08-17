import chromadb

client = chromadb.PersistentClient(
    path="../chroma_db"
)

collection = client.get_collection(
    name="documents"
)

results = collection.get(
    where={
        "tenant_id": "tenant_001"
    },
    include=["documents", "metadatas"]
)

print("Number of chunks:", len(results["ids"]))

for i in range(min(3, len(results["ids"]))):
    print("=" * 50)
    print("ID:", results["ids"][i])
    print("Metadata:", results["metadatas"][i])
    print("Text:", results["documents"][i][:300])