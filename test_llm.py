from app.llm.ollama_llm import OllamaLLM

llm = OllamaLLM()

response = llm.generate(
    "Explain what Retrieval Augmented Generation is in 3 sentence"
)

print(response)