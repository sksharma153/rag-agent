from ollama import Client
from app.llm.base_llm import BaseLLM

class OllamaLLM(BaseLLM):

    def __init__(self):
        self.client = Client()
        self.model = "qwen2.5:7b"

    def generate(self, prompt: str) -> str:

        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )

        return response.message.content