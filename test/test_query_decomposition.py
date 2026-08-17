from app.llm.ollama_llm import OllamaLLM
from app.services.query_decomposer import QueryDecomposer

llm = OllamaLLM()
decomposer = QueryDecomposer(llm)

question = """
Compare Sandeep's Kafka and Spark experience and explain
which one was used more for real-time processing.
"""

conversation_history = []
sub_questions = decomposer.decompose(
    question=question,
    conversation_history=conversation_history,
)

print("=" * 80)
print("Original Question:")
print(question)
print("\nSub-Questions:")

for i, sub_question in enumerate(sub_questions, 1):
    print(f"{i}. {sub_question}")

print("=" * 80)