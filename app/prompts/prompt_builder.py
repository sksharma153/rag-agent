from app.model.retrieved_chunk import RetrievedChunk


class PromptBuilder:
    @staticmethod
    def build(
            question: str,
            chunks: list[RetrievedChunk],
    ) -> str:
        context = "\n\n".join(
            chunk.text for chunk in chunks
        )

        return f"""
You are an expert assistant.

Answer ONLY from the provided context.

If the answer isn't present
say you don't know.

Context
----------------

{context}

----------------

Question:

{question}

Answer:
"""