import re
import uuid

from app.chunking.base_chunker import BaseChunker
from app.model.chunk import DocumentChunk
from app.model.document import ParsedDocument


class HeaderChunker(BaseChunker):

    HEADER_PATTERN = re.compile(
        r"^(#{1,6})\s+(.+?)\s*$",
        re.MULTILINE,
    )

    def chunk(
        self,
        document: ParsedDocument,
    ) -> list[DocumentChunk]:

        content = document.content.strip()

        if not content:
            return []

        matches = list(
            self.HEADER_PATTERN.finditer(content)
        )

        # ---------------------------------------------------------
        # No markdown headers
        # ---------------------------------------------------------

        if not matches:
            return [
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    text=content,
                    metadata={
                        **document.metadata,
                        "filename": document.filename,
                        "chunk_type": "section",
                        "heading": "",
                        "heading_path": [],
                    },
                )
            ]

        chunks = []

        # Header hierarchy.
        #
        # Example:
        #
        # ## Policy Details
        # ### Basic Information
        # #### Premium
        #
        # heading_stack will contain the current hierarchy.
        heading_stack = []

        for index, match in enumerate(matches):

            level = len(match.group(1))
            heading_text = match.group(2).strip()

            start = match.start()

            if index + 1 < len(matches):
                end = matches[index + 1].start()
            else:
                end = len(content)

            section_text = content[
                start:end
            ].strip()

            # -----------------------------------------------------
            # Maintain heading hierarchy
            # -----------------------------------------------------

            heading_stack = [
                item
                for item in heading_stack
                if item["level"] < level
            ]

            heading_stack.append(
                {
                    "level": level,
                    "heading": heading_text,
                }
            )

            heading_path = [
                item["heading"]
                for item in heading_stack
            ]

            # -----------------------------------------------------
            # Create section chunk
            # -----------------------------------------------------

            search_text = (
                f"SECTION: {heading_text}\n\n"
                f"CONTENT:\n{section_text}"
            )

            chunks.append(
                DocumentChunk(
                    id=str(uuid.uuid4()),
                    text=section_text,
                    metadata={
                        **document.metadata,
                        "filename": document.filename,
                        "chunk_type": "section",
                        "heading": heading_text,
                        "heading_level": level,
                        "heading_path": heading_path,
                        "section_index": len(chunks),
                        "search_text": search_text,
                    },
                )
            )

        return chunks