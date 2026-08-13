from abc import ABC, abstractmethod
from app.model.chunk import DocumentChunk
from app.model.retrieved_chunk import RetrievedChunk


class BaseVectorStore(ABC):

    @abstractmethod
    def add_chunks(self, chunks: list[DocumentChunk]):
        pass

    @abstractmethod
    def similarity_search(
            self,
            query_embedding: list[float],
            k: int = 5, 
            tenant_id: str | None = None,
            document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        pass

    @abstractmethod
    def list_documents(self):
        pass

    @abstractmethod
    def delete_documents(self, document_id: str):
        pass
