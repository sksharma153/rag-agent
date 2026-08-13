from app.retrieval.reranker import Reranker

reranker = Reranker()
results = [
    {
        "chunk": type(
            "Chunk",
            (),
            {
                "text": (
                    "Senior Data Engineer with 8+ years "
                    "of experience in designing and "
                    "optimizing large-scale data pipelines."
                )
            },
        )()
    },
    {
        "chunk": type(
            "Chunk",
            (),
            {
                "text": (
                    "Technical Skills: Java, Python, "
                    "Scala, SQL, Spark, Kafka."
                )
            },
        )()
    },
]

reranked = reranker.rerank(
    question="How many years of experience?",
    results=results,
    k=2,
)

for result in reranked:

    print("=" * 80)

    print(
        "Rerank score:",
        result["rerank_score"],
    )

    print(
        "Text:",
        result["chunk"].text,
    )