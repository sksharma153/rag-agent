from app.services.query_rewriter import QueryRewriter
from app.llm.ollama_llm import OllamaLLM

def main():
    llm = OllamaLLM()

    query_rewriter = QueryRewriter(llm)
    question = "Does he have experience with GCP, Beam and Kafka?"
    conversation_history = []

    rewritten_query = query_rewriter.rewrite(
        question=question,
        conversation_history=conversation_history
    )

    print("\n==============================")
    print("Original Question:")
    print(question)

    print("\nConversation:")
    for message in conversation_history:
        print(
            f"{message['role']}: "
            f"{message['content']}"
        )

    print("\nRewritten Query:")
    print(rewritten_query)

    print("==============================\n")


if __name__ == "__main__":
    main()