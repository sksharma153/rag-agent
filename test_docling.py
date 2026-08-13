from app.parsers.docling_parser import DoclingParser

parser = DoclingParser()

document = parser.parse("documents/sample.pdf")

print(document.filename)
print(document.metadata)
print(document.content[:1000])