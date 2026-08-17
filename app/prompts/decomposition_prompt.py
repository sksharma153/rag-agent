DECOMPOSITION_ANSWER_PROMPT = """
You are answering a user's question using retrieved evidence.

The original question may contain multiple information needs.
The evidence below is grouped by sub-question.

Your task is to synthesize the evidence and answer the ORIGINAL question.

Rules:

1. Answer the original question directly.
2. Use only the supplied evidence.
3. Do not invent facts.
4. Do not assume information that is not present in the evidence.
5. When comparing items, use evidence from the relevant sub-questions.
6. If the evidence is insufficient for part of the question, say so.
7. Do not mention the retrieval process.
8. Be concise but complete.

Original Question:

{original_question}

Retrieved Evidence:

{context}

Answer:
"""

def build_decomposition_context(
        original_question: str,
        decomposed_context: list,
) -> str:

    sections = []

    for item in decomposed_context:
        sub_question = item['sub_question']
        chunks = item['chunks']

        context = "\n\n".join(
            chunk.text
            for chunk in chunks
        )

        sections.append(
            f"""Sub-question: {sub_question}
                Evidence: {context} """
        )

    context = "\n\n".join(sections)

    return DECOMPOSITION_ANSWER_PROMPT.format(
        original_question=original_question,
        context=context,
    )