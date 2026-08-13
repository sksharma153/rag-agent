import chromadb

from app.model.chunk import DocumentChunk
from app.model.retrieved_chunk import RetrievedChunk
from app.vectorstore.base_vectorstore import BaseVectorStore

class ChromeVectorStore(BaseVectorStore):
    def __init__(
            self,
            path: str = "chroma_db",
            collection_name: str = "documents"
    ):
        self.client = chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[DocumentChunk]):
        self.collection.add(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks]
        )

    def similarity_search(
            self,
            query_embedding: list[float],
            k: int = 5,
            tenant_id: str | None = None,
            document_ids: list[str] | None = None,
    ) :

        filters = []

        if tenant_id:
            filters.append({"tenant_id": tenant_id})

        if document_ids:
            filters.append({
                "document_id": {
                    "$in": document_ids
                }
            })

        where = None

        if len(filters) == 1:
            where = filters[0]

        elif len(filters) > 1:
            where = {
                "$and": filters
            }

        query = {
            "query_embeddings": [query_embedding],
            "n_results": k
        }

        if where:
            query["where"] = where

        results = self.collection.query(**query)

        retrieved = []

        for i in range(len(results["ids"][0])):
            distance = results["distances"][0][i]
            retrieved.append(
                RetrievedChunk(
                    id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    score=1-distance,
                    metadata=results["metadatas"][0][i],
                )
            )
        return retrieved

    def list_documents(self):

        results = self.collection.get(
            include=["metadatas"]
        )

        documents = {}

        for metadata in results["metadatas"]:

            document_id = metadata.get("document_id")

            if document_id not in documents:
                documents[document_id] = {
                    "document_id": document_id,
                    "filename": metadata["filename"],
                    "content_hash": metadata["content_hash"],
                    "chunk-count": 0
                }

            documents[document_id]["chunk-count"] += 1

        return list(documents.values())

    def delete_documents(self, document_ids):

        results = self.collection.get(
            where={
                "document_id": document_ids
            }
        )

        ids = results["ids"]

        if ids:
            self.collection.delete(
                ids=ids,
            )

        return len(ids)