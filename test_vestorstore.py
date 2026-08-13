from app.parsers.docling_parser import DoclingParser
from app.chunking.header_chunker import HeaderChunker
from app.embeddings.local_embedding import LocalEmbedding
from app.vectorstore.chroma_vectorstore import ChromeVectorStore

parser = DoclingParser()
chunker = HeaderChunker()
embedding = LocalEmbedding()
vectorstore = ChromeVectorStore()

document = parser.parse("documents/sample.pdf")

vector = embedding.embed_text("Hello World")

print(type(vector))
print(len(vector))
print(vector[:5])

chunks = chunker.chunk(document)

for chunk in chunks:
    chunk.embedding = embedding.embed_text(chunk.text)

    print("Chunk ID:", chunk.id)
    print("Embedding is None:", chunk.embedding is None)

    if chunk.embedding is not None:
        print("Embedding length:", len(chunk.embedding))

vectorstore.add_chunks(chunks)

print(f"Indexed {len(chunks)} chunks successfully")

query = "What are the prerequisites for the exam?"

query_embedding = embedding.embed_text(query)

results = vectorstore.similarity_search(query_embedding)

print(results["documents"][0][0])
