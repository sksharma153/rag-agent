from app.model.retrieved_chunk import RetrievedChunk


class PromptBuilder:

    @staticmethod
    def build(
        question: str,
        chunks: list[RetrievedChunk],
    ) -> str:

        context = "\n\n".join(
            chunk.text
            for chunk in chunks
        )

        return f"""
You are an expert assistant answering questions using
retrieved evidence from a document.

Your answer MUST be based ONLY on the provided context.

==================== RULES ====================

1. Answer the user's EXACT question.

2. Do not change the meaning or intent of the question.

3. For factual questions, provide the exact fact requested
   when it is present in the context.

   Examples:
   - If asked for a policy number, give the policy number.
   - If asked for an amount, give the amount.
   - If asked for a date, give the date.
   - If asked for a person's name, give the name.
   - If asked for a percentage, give the percentage.

4. Do not replace a factual answer with a definition or
   general explanation.

5. For questions asking for multiple pieces of information,
   answer ALL requested parts.

6. Do not add unrelated information from other retrieved chunks.

7. Keep the answer focused and concise.

8. Do not invent, infer, or assume information that is not
   supported by the context.

9. If the exact information needed to answer the question
   is not present in the context, say:
   "I don't know based on the provided context."

10. When the context contains the answer, do not say
    "I don't know."

11. For comparisons, explicitly compare the requested items.

12. For procedural questions, provide the actual procedure
    described in the context rather than summarizing unrelated
    policy sections.

==================== CONTEXT ====================

{context}

==================== QUESTION ====================

{question}

==================== ANSWER ====================

Answer directly and concisely:
"""