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
        question = question.strip()

        if self._should_not_decompose(question):
            return [question]

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

        if self._looks_like_simple_field_lookup(question, sub_questions):
            return [question]

        return sub_questions[:4]

    def _should_not_decompose(
            self,
            question: str,
    ) -> bool:

        q = question.lower().strip()

        # Simple factual / lookup patterns
        prefixes = (
            "what is ",
            "what are ",
            "who is ",
            "who are ",
            "when is ",
            "when was ",
            "where is ",
            "where was ",
            "how much ",
            "how many ",
        )

        if q.startswith(prefixes):
            comparison_words = (
                "compare",
                "difference",
                "versus",
                " vs ",
                "which one",
                "why",
            )

            if not any(
                word in q
                for word in comparison_words
            ):
                return True

        return False

    def _looks_like_simple_field_lookup(
            self,
            question: str,
            sub_question: list,
    ) -> bool:

        if len(sub_question) <= 1:
            return False

        q = question.lower()

        # Common multi-field lookup:
        # "What is X and Y?"
        if (
                q.startswith("what is ")
                and " and " in q
                and not any(
                word in q
                for word in [
                    "compare",
                    "difference",
                    "versus",
                    " vs ",
                ]
            )
        ):
            return True

        # "Who is X and Y?"
        if (
            q.startswith("who is ")
            and " and " in q
        ):
            return True
        return False