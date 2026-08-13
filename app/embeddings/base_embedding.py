from abc import ABC, abstractmethod

class BaseEmbedding(ABC):

    @abstractmethod
    def embed_text(self, text: str):
        pass

    @abstractmethod
    def embed_documents(self, documents):
        pass