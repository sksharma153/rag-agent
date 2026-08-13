from abc import ABC, abstractmethod

from app.model.chunk import DocumentChunk
from app.model.document import ParsedDocument


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, document: ParsedDocument) -> list[DocumentChunk]:
        pass