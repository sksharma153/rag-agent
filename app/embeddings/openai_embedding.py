from openai import OpenAI

from app.config.settings import get_settings
from app.embeddings.base_embedding import BaseEmbedding

class OpenAIEmbedding(BaseEmbedding):

    def __init__(self):
        settings = get_settings()

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"

    def embed_text(self, text: str):
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        return response.data[0].embedding

    def embed_documents(self, documents):
        response = self.client.embeddings.create(
            model=self.model,
            input=documents
        )

        return [item.embedding for item in response.data]