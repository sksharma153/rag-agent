import re
from app.prompts.query_decomposition_prompt import QUERY_DECOMPOSITION_PROMPT

class QueryDecomposer:
    def __init__(self, llm):
        self.llm = llm

    def decompose(
            self,
            question: str,
            conversation_history: list | None = None,
    ) -> list:

        conversation_history = conversation_history or []
        history_text = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in conversation_history
        )

        prompt = QUERY_DECOMPOSITION_PROMPT.format(
            conversation_history=history_text,
            question=question,
        )

        response = self.llm.generate(prompt)

        if not response:
            return [question]

        sub_questions = []

        for line in response.splitlines():
            line = line.strip()
            if not line:
                continue

            line = re.sub(
                r"^\s*\d+[\.\)\-:]\s*",
                "",
                line,
            )

            line = line.strip()

            if line:
                sub_questions.append(line)

        if not sub_questions:
            return [question]

        return sub_questions[:4]