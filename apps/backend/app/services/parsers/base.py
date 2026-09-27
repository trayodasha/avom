from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class PageContent:
    page_number: int
    text: str


@dataclass
class ParsedDocument:
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    pages: List[PageContent] = field(default_factory=list)


class BaseParser(ABC):
    @abstractmethod
    def parse(self, content: bytes, filename: str) -> ParsedDocument:
        """Parse raw document byte content into clean extracted text and page structures."""
        pass
