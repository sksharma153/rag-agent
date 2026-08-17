from app.chunking.header_chunker import HeaderChunker
from app.embeddings.local_embedding import LocalEmbedding
from app.parsers.docling_parser import DoclingParser
from app.services.ingestion_service import IngestionService
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

service = IngestionService(
    parser=DoclingParser(),
    chunker=HeaderChunker(),
    embedding=LocalEmbedding(),
    vectorstore=ChromeVectorStore(),
)

count = service.ingest("documents/sample.pdf")

print(f"{count} chunks indexed")