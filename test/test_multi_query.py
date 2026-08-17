from app.llm.ollama_llm import OllamaLLM
from app.services.multi_query_generator import MultiQueryGenerator

llm = OllamaLLM()
generator = MultiQueryGenerator(llm)

question = """
What technologies does Sandeep use for real-time data processing?
"""

queries = generator.generate(question)

print("=" * 80)
print("Original Query:")
print(question)

print("\nGenerated Queries:")

for i, query in enumerate(queries, 1):
    print(f"{i}. {query}")

print("=" * 80)
