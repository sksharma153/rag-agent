import chromadb
from pathlib import Path
from app.model.chunk import DocumentChunk
from app.model.retrieved_chunk import RetrievedChunk
from app.vectorstore.base_vectorstore import BaseVectorStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]

class ChromeVectorStore(BaseVectorStore):
    def __init__(
            self,
            path: str | None = None,
            collection_name: str = "documents"
    ):
        if path is None:
            path = str(
                PROJECT_ROOT/"chroma_db"
            )
        self.client = chromadb.PersistentClient(path=path)

        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        """
        self.child_collection = (
            self.client.get_or_create_collection(
                name="document_children",
                metadata={"hnsw:space": "cosine"},
            )
        )

        self.parent_collection = (
            self.client.get_or_create_collection(
                name="document_parents",
            )
        )"""

    def add_chunks(self, chunks: list[DocumentChunk]):
        self.child_collection.add(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.metadata.get("search_text", chunk.text) for chunk in chunks],
            embeddings=[chunk.embedding for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks]
        )
        self.add_children(chunks)

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

        results = self.child_collection.query(**query)

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

        results = self.child_collection.get(
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
        delete_count = 0
        child_results = self.child_collection.get(
            where={
                "document_id": {
                    "$in": document_ids
                }
            }
        )

        child_ids = child_results["ids"]

        if child_ids:
            self.child_collection.delete(
                ids=child_ids,
            )
            delete_count += len(child_ids)

        parent_results = self.parent_collection.get(
            where={
                "document_id": {
                    "$in": document_ids
                }
            }
        )
        parent_ids = parent_results["ids"]
        if parent_ids:
            self.parent_collection.delete(
                ids=parent_ids,
            )

        return delete_count

    def add_parents(self, chunks):
        self.parent_collection.add(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[
                chunk.metadata for chunk in chunks
            ]
        )

    def get_parents(self, parent_id: str):
        result = self.parent_collection.get(
            ids=[parent_id]
        )

        if not result["ids"]:
            return None

        return RetrievedChunk(
            id=result["ids"][0],
            text=result["documents"][0],
            score=1.0,
            metadata=result["metadatas"][0]
        )

    def add_children(
            self,
            chunks: list[DocumentChunk],
    ):
        if not chunks:
            return

        self.child_collection.add(
            ids=[
                chunk.id
                for chunk in chunks
            ],
            documents=[
                chunk.text
                for chunk in chunks
            ],
            embeddings=[
                chunk.embedding
                for chunk in chunks
            ],
            metadatas=[
                chunk.metadata
                for chunk in chunks
            ],
        )