
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

        parent_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("chunk_type") == "parent"
        ]

        child_chunks = [
            chunk for chunk in chunks if chunk.metadata.get("chunk_type") == "child"
        ]

        for index, chunk in enumerate(child_chunks):
            #chunk.id = f"{document_id}:{index}"
            chunk.metadata.update({
                'document_id': document_id,
                'tenant_id': tenant_id,
                'filename': document.filename,
                'chunk_index': index,
                'content_hash': content_hash,
            })

        texts = [chunk.text for chunk in child_chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        for chunk, embedding in zip(child_chunks, embeddings):
            chunk.embedding = embedding

        #-------------------------------
        # Adding chunks to ChromaDb
        #-------------------------------
        #self.vectorstore.add_chunks(chunks)

        if parent_chunks:
            self.vectorstore.add_parents(parent_chunks)
        if child_chunks:
            self.vectorstore.add_children(child_chunks)

        #-------------------------------
        # Adding chunks to BM25
        #-------------------------------
        if child_chunks:
            self.bm25_retriever.add_chunks(
                tenant_id=tenant_id,
                chunks=child_chunks,
            )

        return {
            "document_id": document_id,
            "tenant_id": tenant_id,
            "filename": document.filename,
            "content_hash": content_hash,
            "parent_created": len(parent_chunks),
            "children_created": len(child_chunks),
            "status": "indexed"
        }
