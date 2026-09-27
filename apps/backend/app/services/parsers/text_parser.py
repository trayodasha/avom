from typing import Dict, Any
from app.services.parsers.base import BaseParser, ParsedDocument, PageContent


class TextParser(BaseParser):
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        # Try UTF-8 first, fallback to latin-1
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1", errors="replace")

        # Clean null bytes and carriage returns
        cleaned_text = text.replace("\x00", "").replace("\r\n", "\n")
        metadata: Dict[str, Any] = {
            "source": filename,
            "char_count": len(cleaned_text),
            "line_count": len(cleaned_text.splitlines())
        }
        pages = [PageContent(page_number=1, text=cleaned_text)]
        return ParsedDocument(text=cleaned_text, metadata=metadata, pages=pages)
