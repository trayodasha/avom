import io
from typing import Dict, Any, List
from pypdf import PdfReader
from app.services.parsers.base import BaseParser, ParsedDocument, PageContent


class PDFParser(BaseParser):
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        stream = io.BytesIO(content)
        reader = PdfReader(stream)
        pages: List[PageContent] = []
        full_text_list: List[str] = []

        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            cleaned_page = page_text.replace("\x00", "").strip()
            pages.append(PageContent(page_number=idx + 1, text=cleaned_page))
            if cleaned_page:
                full_text_list.append(cleaned_page)

        full_text = "\n\n".join(full_text_list)
        metadata: Dict[str, Any] = {
            "source": filename,
            "page_count": len(reader.pages),
            "char_count": len(full_text),
        }
        return ParsedDocument(text=full_text, metadata=metadata, pages=pages)
