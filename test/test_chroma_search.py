import chromadb

from app.embeddings.local_embedding import LocalEmbedding


CHROMA_PATH = "../chroma_db"
COLLECTION_NAME = "document_children"
TENANT_ID = "tenant_001"

QUESTION = "What is the maturity date?"


print("=" * 80)
print("CHROMA DEBUG")
print("=" * 80)

print("Chroma path:", CHROMA_PATH)
print("Collection:", COLLECTION_NAME)
print("Tenant:", TENANT_ID)
print("Question:", QUESTION)

# ---------------------------------------------------------
# Connect
# ---------------------------------------------------------

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

print("\nConnected to Chroma")

# ---------------------------------------------------------
# List collections
# ---------------------------------------------------------

collections = client.list_collections()

print("\nCollections:")

for collection in collections:
    print(
        "-",
        collection.name
    )

# ---------------------------------------------------------
# Get collection
# ---------------------------------------------------------

try:

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    print(
        "documents:",
        client.get_collection("documents").count()
    )

    print(
        "document_children:",
        client.get_collection("document_children").count()
    )

    print(
        "document_parents:",
        client.get_collection("document_parents").count()
    )

except Exception as exc:

    print(
        "\nERROR getting collection:",
        exc
    )

    raise

# ---------------------------------------------------------
# Collection count
# ---------------------------------------------------------

count = collection.count()

print(
    "\nCollection document count:",
    count
)

if count == 0:

    print(
        "\nWARNING: collection is empty."
    )

    raise SystemExit(0)

# ---------------------------------------------------------
# Embedding
# ---------------------------------------------------------

embedding_service = LocalEmbedding()

print(
    "\nGenerating query embedding..."
)

query_embedding = (
    embedding_service.embed_text(
        text=QUESTION
    )
)

print(
    "Embedding size:",
    len(query_embedding)
)

# ---------------------------------------------------------
# Query
# ---------------------------------------------------------

print(
    "\nRunning vector search..."
)

results = collection.query(
    query_embeddings=[
        query_embedding
    ],
    n_results=5,
    where={
        "tenant_id": TENANT_ID
    },
    include=[
        "documents",
        "metadatas",
        "distances",
    ],
)

# ---------------------------------------------------------
# Result summary
# ---------------------------------------------------------

ids = results.get(
    "ids",
    [[]],
)[0]

print(
    "\nResult count:",
    len(ids)
)

if not ids:

    print(
        "\nNO RESULTS FOUND"
    )

    print(
        "\nCheck that the collection contains "
        "documents with tenant_id =",
        TENANT_ID,
    )

    raise SystemExit(0)

# ---------------------------------------------------------
# Print results
# ---------------------------------------------------------

for i in range(len(ids)):

    distance = (
        results["distances"][0][i]
    )

    metadata = (
        results["metadatas"][0][i]
    )

    text = (
        results["documents"][0][i]
    )

    print("\n" + "=" * 80)

    print(
        "RANK:",
        i + 1
    )

    print(
        "ID:",
        ids[i]
    )

    print(
        "Distance:",
        distance
    )

    print(
        "Similarity:",
        1 - distance
    )

    print(
        "Heading:",
        metadata.get(
            "heading"
        )
    )

    print(
        "Chunk type:",
        metadata.get(
            "chunk_type"
        )
    )

    print(
        "Text:"
    )

    print("Metadata:", metadata)

    print(
        "Search Text:",
        metadata.get(
            "search_text",
            "NOT_PRESENT",
        )[:500]
    )

    print(
        "Text:",
        text[:500]
    )

    print(
        text[:1000]
    )
