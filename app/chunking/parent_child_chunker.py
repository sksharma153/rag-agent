import re
import uuid

from app.chunking.base_chunker import BaseChunker
from app.model.chunk import DocumentChunk
from app.model.document import ParsedDocument


class ParentChildChunker(BaseChunker):
    def __init__(
            self,
            child_size: int = 1200,
            child_overlap: int = 200
    ):
        self.child_size = child_size
        self.child_overlap = child_overlap

    def chunk(
            self,
            document: ParsedDocument,
    ) -> list[DocumentChunk]:
        sections = re.split(
            r"(?=^#{1,6}\s)",
            document.content,
            flags=re.MULTILINE,
        )

        chunks = []

        document_id = document.metadata['document_id']
        if not document_id:
            raise ValueError(
                "document_id is required in document.metadata before chunking."
            )

        for parent_index, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue

            parent_id = f"{document_id}:P{parent_index}"
            heading_match = re.match(
                r"^(#{1,6}\s+.+?)(?:\n|$)",
                section,
            )

            heading = (
                heading_match.group(1).strip() if heading_match else ""
            )

            # Parent chunks
            parent_metadata = {
                **document.metadata,
                "filename": document.filename,
                "chunk_type": "parent",
                "parent_id": parent_id,
                "parent_index": parent_index,
                "heading": heading,
            }

            parent_chunk = DocumentChunk(
                id = parent_id,
                text = section,
                metadata = parent_metadata,
            )
            chunks.append(parent_chunk)

            #child chunks
            children = self._split_text(section)

            for child_index, child_text in enumerate(children):
                child_id = (
                    f"{parent_id}:C{child_index}"
                )

                child_metadata = {
                    **document.metadata,
                    "filename": document.filename,
                    "chunk_type": "child",
                    "parent_id": parent_id,
                    "parent_index": parent_index,
                    "child_index": child_index,
                    "heading": heading,
                }

                child_chunk = DocumentChunk(
                    id = child_id,
                    text = child_text,
                    metadata = child_metadata,
                )
                chunks.append(child_chunk)

        return chunks


    def _split_text(
            self,
            text: str,
    ) -> list[str]:

        if len(text) <= self.child_size:
            return [text]

        children = []
        start = 0
        length = len(text)
        while start < length:
            end = min(start + self.child_size, length)

            child = text[start:end].strip()

            if child:
                children.append(child)

            if end >= length:
                break

            start = max(
                end-self.child_overlap,
                start + 1,
            )
        return children