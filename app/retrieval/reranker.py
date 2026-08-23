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

        pairs = []
        for result in results:
            chunk = result["chunk"]
            parent = result.get("parent")
            heading = ""

            if chunk.metadata:
                heading = chunk.metadata.get("heading", "")

            if parent:
                parent_text = parent.text[:4000]
                candidate_text = (
                    f"SECTION:\n"
                    f"{heading}\n\n"
                    f"PARENT CONTEXT:\n"
                    f"{parent_text}\n\n"
                    f"CHILD CONTENT:\n"
                    f"{chunk.text}"
                )
            else:
                candidate_text = (
                    f"SECTION:\n"
                    f"{heading}\n\n"
                    f"CHILD CONTENT:\n"
                    f"{chunk.text}"
                )

            pairs.append((
                question,candidate_text
            ))

        scores = self.model.predict(pairs)

        reranked = []

        for result, score in zip(results, scores):
            hybrid_score = float(
                result.get("hybrid_score", 0.0)
            )

            final_score = (
                float(score) + 1.0 * hybrid_score
            )
            updated_result = result.copy()
            updated_result["cross_encoder_score"] = float(score)
            updated_result["rerank_score"] = final_score
            reranked.append(updated_result)

        reranked.sort(
            key=lambda x: x["rerank_score"],
            reverse=True
        )

        return reranked[:k]

