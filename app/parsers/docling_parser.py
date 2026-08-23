from pathlib import Path
from docling.document_converter import DocumentConverter

from app.model.document import ParsedDocument


class DoclingParser:
    def __init__(self):
        self.converter = DocumentConverter()

    def parse(self, file_path: str) -> ParsedDocument:
        """
        Parse the document and return markdown
        :param file_path:
        :return:
        """
        print("FilePath: {}".format(file_path))
        file = Path(file_path)
        if not file.is_file():
            raise FileNotFoundError(f"File {file_path} not found")

        result = self.converter.convert(source=str(file))
        markdown = result.document.export_to_markdown()

        return ParsedDocument(
            filename=file.name,
            content=markdown,
            metadata={
                "parsers": "docling",
                "extension": file.suffix,
            },
        )
