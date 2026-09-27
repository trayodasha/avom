import os
from app.services.parsers.base import BaseParser
from app.services.parsers.text_parser import TextParser
from app.services.parsers.pdf_parser import PDFParser
from app.services.parsers.docx_parser import DocxParser


def get_parser(filename_or_ext: str) -> BaseParser:
    ext = os.path.splitext(filename_or_ext)[-1].lower().replace(".", "")
    if ext in ["txt", "md", "markdown", "text", "csv", "json"]:
        return TextParser()
    elif ext == "pdf":
        return PDFParser()
    elif ext in ["docx", "doc"]:
        return DocxParser()
    else:
        # Default fallback to TextParser
        return TextParser()
