from sentence_transformers import CrossEncoder


class Reranker:

    def __init__(
            self,
            model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self.model = CrossEncoder(
            model_name,
            device="cpu",
        )

    def rerank(
            self,
            question: str,
            results: list,
            k: int = 3
    ):

        if not results:
            return []

        pairs = [
            (
                question,
                result["chunk"].text
            )
            for result in results
        ]

        scores = self.model.predict(pairs)

        reranked = []

        for result, score in zip(results, scores):
            updated_result = result.copy()
            updated_result["rerank_score"] = float(score)
            reranked.append(updated_result)

        reranked.sort(
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return reranked[:k]

