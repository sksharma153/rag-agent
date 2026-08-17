from app.prompts.multi_query_prompt import MULTI_QUERY_PROMPT
import re

class MultiQueryGenerator:

    def __init__(self, llm):
        self.llm = llm

    def generate(self, question: str) -> list[str]:

        prompt = MULTI_QUERY_PROMPT.format(question=question)

        response = self.llm.generate(prompt)

        if not response:
            return [question]

        queries = []

        for line in response.splitlines():

            line.strip()
            if not line:
                continue

            line = re.sub(r"^\s*\d+[\.\)\-:]\s*", "", line)

            line = line.strip()
            if line:
                queries.append(line)

        if not queries:
            return [question]

        return [question] + queries[:3]