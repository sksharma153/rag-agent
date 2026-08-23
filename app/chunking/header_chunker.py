"""
import re

from app.chunking.base_chunker import BaseChunker
from app.model.chunk import DocumentChunk
from app.model.document import ParsedDocument

class HeaderChunker(BaseChunker):

    def chunk(self, document: ParsedDocument) -> list[DocumentChunk]:
        sections = re.split(r"(?=^#{1,6}\s)", document.content, flags=re.MULTILINE)

        chunks = []

        document_id = document.metadata.get("document_id")

        if not document_id:
            raise ValueError(
                "document_id is required "
                "before chunking"
            )

        for section in sections:
            section = section.strip()

            if not section:
                continue

            chunks.append(
                DocumentChunk(
                    id="",
                    text=section,
                    metadata={
                        **document.metadata,
                        "filename": document.filename,
                    },
                )
            )

        return chunks
"""