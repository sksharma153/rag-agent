from app.prompts.query_rewriter_prompt import QUERY_REWRITE_PROMPT

class QueryRewriter:

    def __init__(self, llm):
        self.llm = llm

    def rewrite(
            self,
            question: str,
            conversation_history: list | None = None,
    ) -> str:

        conversation_history = conversation_history or []

        if not conversation_history:
            return question.strip()

        history_text = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in conversation_history
        )

        prompt = QUERY_REWRITE_PROMPT.format(
            conversation_history=history_text,
            question=question,
        )

        rewritten_query = self.llm.generate(prompt).strip()

        if not rewritten_query:
            return question

        return rewritten_query