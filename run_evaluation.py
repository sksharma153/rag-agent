from app.api.chat import multi_query_generator
from app.embeddings.local_embedding import LocalEmbedding
from app.evaluation.evaluator import RetrievalEvaluator
from app.llm.ollama_llm import OllamaLLM
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.reranker import Reranker
from app.services.multi_query_generator import MultiQueryGenerator
from app.services.query_rewriter import QueryRewriter
from app.services.retrieval_service import RetrievalService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore


def main():
    embedding_service = LocalEmbedding()
    vectorstore_service = ChromeVectorStore()
    bm25_retriever = BM25Retriever()
    reranker = Reranker()

    hybrid_retriever = HybridRetriever(
        vectorstore=vectorstore_service,
        embedding=embedding_service,
        bm25_retriever=bm25_retriever,
    )

    retrieval_service = RetrievalService(
        hybrid_retriever=hybrid_retriever,
        reranker=reranker,
    )

    llm = OllamaLLM()
    query_rewriter = QueryRewriter(llm)
    multi_query_generator = MultiQueryGenerator(llm)

    evaluator = RetrievalEvaluator(
        retrieval_service=retrieval_service,
        query_rewriter=query_rewriter,
        multi_query_generator=multi_query_generator,
    )

    dataset = evaluator.load_dataset("evaluation/eval_database_gold.json")
    report = evaluator.evaluate_all(dataset=dataset, k=5)

    evaluator.print_comparison(
        evaluations=report,
        k=5
    )

if __name__ == "__main__":
    main()
