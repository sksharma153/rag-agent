from app.parsers.docling_parser import DoclingParser
from app.chunking.header_chunker import HarderChunker

parser = DoclingParser()
chunker = HarderChunker()

document = parser.parse("documents/sample.pdf")

chunks = chunker.chunk(document)

print(f"Chunk Created: {len(chunks)}")

print("=" * 80)

print(chunks[0].text[:1000])