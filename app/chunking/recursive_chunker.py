from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.chunking.base_chunker import BaseChunker
from app.model.chunk import DocumentChunk
from app.model.document import ParsedDocument

import uuid

class RecursiveChunker(BaseChunker):
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter()(
            chunk_size=800,
            chunk_overlap=150,
            separators=[
                "\n## ",
                "\n### ",
                "\n\n",
                "\n",
                ". ",
                " ",
                ""
            ]
        )

    def chunk(self, document: ParsedDocument):
        texts = self.splitter.split_text(document.content)
        chunks = []

        for text in texts:
            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    text=text,
                    metadata={
                        **document.metadata,
                        "filename": document.filename
                    }
                )
            )
        return chunks