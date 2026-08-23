import json
import re

class EvidenceReranker:
    def __init__(self, llm):
        self.llm = llm

    def rerank(self, question: str, results: list, k: int = 5) -> list:
        if not results:
            return []

        scored_results = []

        for index, result in enumerate(results):
            chunk = result["chunk"]
            parent = result.get("parent")

            heading = ""
            if chunk.metadata:
                heading = chunk.metadata.get("heading", "")

            if parent:
                parent_text = parent.text[:3000]
            else:
                parent_text = ""

            child_text = chunk.text[:3000]

            candidate_text = (
                f"SECTION:\n{heading}\n\n"
                f"PARENT:\n{parent_text}\n\n"
                f"CHILD:\n{child_text}"
            )

            score_data = self._score_candidate(
                question=question,
                candidate_text=candidate_text,
            )

            scored_results.append(
                {
                    **result,
                    "evidence_score": score_data["score"],
                    "evidence_reason": score_data["reason"],
                    "answerable": score_data["answerable"],
                }
            )

        scored_results.sort(
            key=lambda x: x["evidence_score"],
            reverse=True
        )

        return scored_results[:k]

    def _score_candidate(
            self,
            question: str,
            candidate_text: str
    )-> dict:
        prompt = f"""
        You are a retrieval evidence evaluator.

        Your job is NOT to answer the user's question.

        Determine whether the candidate contains the
        specific information needed to answer the question.

        QUESTION:
        {question}

        CANDIDATE:
        {candidate_text}

        Evaluate the candidate using these rules:

        1. Score HIGH when the candidate directly contains
           the requested answer or the exact evidence needed
           to answer it.

        2. Score MEDIUM when the candidate is strongly related
           but does not contain the requested value/evidence.

        3. Score LOW when the candidate only defines, explains,
           or discusses the topic without providing the requested
           information.

        4. Prefer answer-bearing records over general definitions.

        5. Do not infer information that is not present.

        Return ONLY valid JSON:

        {{
            "answerable": true,
            "score": 0.0,
            "reason": "brief explanation"
        }}

        The score must be between 0 and 1.
        """

        response = self.llm.generate(prompt)
        parsed = self._parse_json(response)

        if parsed is None:
            return {
                "answerable": False,
                "score": 0.0,
                "reason": "Invalid evaluator response"
            }
        return {
            "answerable": bool(
                parsed.get("answerable", False)
            ),
            "score": self._safe_score(
                parsed.get("score", 0.0),
            ),
            "reason": str(
                parsed.get("reason", "")
            )
        }

    @staticmethod
    def _safe_score(value) -> float:

        try:
            score = float(value)
        except (
                TypeError,
                ValueError,
        ):
            return 0.0

        return max(
            0.0,
            min(1.0, score),
        )

    @staticmethod
    def _parse_json(
            response: str,
    ):

        if not response:
            return None

        response = response.strip()

        # Remove markdown code fences if Ollama adds them.
        response = re.sub(
            r"^```json\s*",
            "",
            response,
            flags=re.IGNORECASE,
        )

        response = re.sub(
            r"^```\s*",
            "",
            response,
        )

        response = re.sub(
            r"\s*```$",
            "",
            response,
        )

        try:
            return json.loads(response)
        except json.JSONDecodeError:

            # Try extracting the first JSON object.
            match = re.search(
                r"\{.*\}",
                response,
                flags=re.DOTALL,
            )

            if not match:
                return None

            try:
                return json.loads(
                    match.group(0)
                )
            except json.JSONDecodeError:
                return None