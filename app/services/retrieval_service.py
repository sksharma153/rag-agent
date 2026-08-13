class RetrievalService:

    def __init__(
            self,
            hybrid_retriever,
            reranker
    ):
        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker

    def retrieve(
            self,
            question: str,
            tenant_id: str,
            document_id: str | None = None,
            k: int = 3,
    ):

        # Get the larger candidate set first
        candidates = self.hybrid_retriever.retrieve(question, tenant_id, document_id, k=10)

        # Rerank the candidates
        results = self.reranker.rerank(question, candidates, k=k)

        return results