from app.parsers.docling_parser import DoclingParser
from app.chunking.header_chunker_v2 import HeaderChunker


parser = DoclingParser()
chunker = HeaderChunker()

document = parser.parse(
    "/Users/sandeepkumarsharma/Downloads/Agents-Workspace/rag-agent/documents/PolicyInformationPage.pdf"
)

chunks = chunker.chunk(document)

print("CHUNK COUNT:", len(chunks))

for chunk in chunks[:20]:

    print("\n" + "=" * 80)

    print("ID:", chunk.id)

    print(
        "TYPE:",
        chunk.metadata.get("chunk_type")
    )

    print(
        "HEADING:",
        chunk.metadata.get("heading")
    )

    print(
        "LEVEL:",
        chunk.metadata.get("heading_level")
    )

    print(
        "PATH:",
        chunk.metadata.get("heading_path")
    )

    print(
        "TEXT:",
        chunk.text[:300]
    )

    print(
        "SEARCH TEXT:",
        chunk.metadata.get("search_text", "")[:300]
    )