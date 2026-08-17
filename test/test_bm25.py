from app.retrieval.bm25_retriever import BM25Retriever
from app.chunking.header_chunker import HeaderChunker
from app.parsers.docling_parser import DoclingParser

parser = DoclingParser()
chunker = HeaderChunker()

document = parser.parse("documents/Sandeep_resume.pdf")

chunks = chunker.chunk(document)

retriever = BM25Retriever()

retriever.add_chunks(
    tenant_id="tenant_001",
    chunks=chunks,
)

results = retriever.search(
    tenant_id="tenant_001",
    query="How many years of experience?",
    k=5
)

for result in results:
    print("=" * 80)
    print(
        "Score:",
        result["score"]
    )

    print(
        "Text:",
        result["chunk"].text[:500]
    )