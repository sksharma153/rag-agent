
from app.utils.file_utils import calculate_file_hash

import uuid

class IngestionService:

    def __init__(
            self,
            parser,
            chunker,
            embedding_service,
            vectorstore,
            bm25_retriever,
    ):
        self.parser = parser
        self.vectorstore = vectorstore
        self.chunker = chunker
        self.embedding_service = embedding_service
        self.bm25_retriever = bm25_retriever

    def ingest(self, file_path: str, tenant_id: str):
        document_id = str(uuid.uuid4())
        content_hash = calculate_file_hash(file_path)
        document = self.parser.parse(file_path)
        document.metadata.update({
            "document_id": document_id,
            "tenant_id": tenant_id,
            "content_hash": content_hash,
        })
        chunks = self.chunker.chunk(document)

        for index, chunk in enumerate(chunks):
            chunk.id = f"{document_id}:{index}"
            chunk.metadata.update({
                'document_id': document_id,
                'tenant_id': tenant_id,
                'filename': document.filename,
                'chunk_index': index,
                'content_hash': content_hash,
            })

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        #-------------------------------
        # Adding chunks to ChromaDb
        #-------------------------------
        self.vectorstore.add_chunks(chunks)

        #-------------------------------
        # Adding chunks to BM25
        #-------------------------------
        self.bm25_retriever.add_chunks(
            tenant_id=tenant_id,
            chunks=chunks,
        )

        return {
            "document_id": document_id,
            "tenant_id": tenant_id,
            "filename": document.filename,
            "content_hash": content_hash,
            "chunks_created": len(chunks),
            "status": "indexed"
        }
