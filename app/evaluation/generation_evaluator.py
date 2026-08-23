import re
import json

def parse_judge_response(judge_response: str) -> dict:
    """
        Robustly parse JSON returned by the judge LLM.
        Handles:
          1. Plain JSON
          2. Markdown fenced JSON
          3. JSON embedded in surrounding text
    """
    text = judge_response.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL,
    )

    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    start = text.find('{')
    end = text.find('}')

    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return {
        "score": None,
        "faithfulness": None,
        "context_relevance": None,
        "reason": {
            "Unable to parse judge response: " + text
        }
    }

class GenerationEvaluator:
    def __init__(
            self,
            rag_service,
            judge_llm
    ):
        self.rag_service = rag_service
        self.judge_llm = judge_llm

    def evaluate(
            self,
            question: str,
            expected_answer: str,
            tenant_id: str,
            document_id: str,
    ):
        response = self.rag_service.ask(
            question=question,
            tenant_id=tenant_id,
            document_id=document_id,
            conversation_history=[]
        )

        if not response:
            raise ValueError(
                "RagService.ask() returned None"
            )

        answer = response.get('answer')
        context = response.get('context', "")

        correctness_prompt = f"""
        You are an expert evaluator of a Retrieval-Augmented
        Generation system.

        Your job is to determine whether the GENERATED ANSWER
        correctly answers the QUESTION when compared with the
        EXPECTED ANSWER.

        QUESTION:
        {question}

        EXPECTED ANSWER:
        {expected_answer}

        GENERATED ANSWER:
        {answer}

        Evaluation rules:

        1. Evaluate semantic meaning, not exact wording.

        2. Paraphrases are acceptable.

        3. Different sentence structures are acceptable.

        4. Equivalent values, dates, names, identifiers, and facts
           should be considered correct even when written differently.

        5. If the question asks multiple things, all important
           parts must be answered.

        6. Extra information does not automatically make an answer
           incorrect. However, unsupported or contradictory claims
           should reduce the score.

        7. If the generated answer is correct but more concise than
           the expected answer, it should still receive a high score.

        8. If the answer is partially correct, give a partial score.

        Scoring:

        1.0 = fully correct
        0.8 = mostly correct with only minor omission
        0.6 = substantially correct but incomplete
        0.4 = partially correct
        0.2 = very limited correctness
        0.0 = incorrect or does not answer the question

        Return ONLY valid JSON.

        Do not use Markdown.
        Do not use ```json.
        Do not add text before or after the JSON.

        {{
            "answer_correctness": 0.0,
            "reason": "brief explanation"
        }}
        """

        correctness_raw = (
            self.judge_llm.generate(
                correctness_prompt,
            )
        )

        correctness_eval = parse_judge_response(correctness_raw)

        grounding_prompt = f"""
        You are an expert evaluator of a
        Retrieval-Augmented Generation system.

        QUESTION:
        {question}

        RETRIEVED CONTEXT:
        {context}

        GENERATED ANSWER:
        {answer}

        Evaluate the following two dimensions.

        1. FAITHFULNESS

        Are the factual claims in the generated answer
        supported by the retrieved context?

        1.0 = all important claims are supported
        0.8 = almost all claims are supported
        0.6 = mostly supported with minor unsupported claims
        0.4 = significant unsupported claims
        0.2 = mostly unsupported
        0.0 = major claims are unsupported or contradicted

        2. CONTEXT_RELEVANCE

        How useful is the retrieved context for answering
        the question?

        1.0 = directly contains the information needed
        0.8 = highly relevant with minor noise
        0.6 = moderately relevant
        0.4 = partially relevant
        0.2 = mostly irrelevant
        0.0 = irrelevant

        Important:

        - Judge ONLY the supplied context.
        - Do not use outside knowledge.
        - Do not use the expected answer.
        - Do not assume facts that are not present in the context.
        - Extra context is acceptable if it does not prevent the
          necessary evidence from being available.

        Return ONLY valid JSON.

        Do not use Markdown.
        Do not use ```json.
        Do not add text before or after the JSON.

        {{
            "faithfulness": 0.0,
            "context_relevance": 0.0,
            "reason": "brief explanation"
        }}
        """

        grounding_raw = (
            self.judge_llm.generate(
                grounding_prompt,
            )
        )

        grounding_eval = parse_judge_response(grounding_raw)
        evaluation = {
            "answer_correctness":
                correctness_eval.get(
                    "answer_correctness"
                ),

            "faithfulness":
                grounding_eval.get(
                    "faithfulness"
                ),

            "context_relevance":
                grounding_eval.get(
                    "context_relevance"
                ),

            "correctness_reason":
                correctness_eval.get(
                    "reason",
                    "",
                ),

            "grounding_reason":
                grounding_eval.get(
                    "reason",
                    "",
                ),
        }

        return {
            "question": question,
            "expected_answer": expected_answer,
            "answer": answer,
            "context": context,
            "evaluation": evaluation,
        }

    def load_dataset(
            self,
            path: str,
    ):
        with open(
                path,
                "r",
                encoding="utf-8",
        ) as file:
            return json.load(file)