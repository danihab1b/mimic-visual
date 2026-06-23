"""Abstract source interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from visrag.core.document import Document


class AbstractSource(ABC):
    @abstractmethod
    def can_handle(self, document: Document) -> bool: ...

    @abstractmethod
    async def fetch_html(self, document: Document) -> str: ...

    @abstractmethod
    async def get_metadata(self, document: Document) -> dict: ...

    @staticmethod
    def resolve(document: Document) -> AbstractSource:
        from visrag.sources.image import ImageSource
        from visrag.sources.local import LocalSource
        from visrag.sources.pdf import PDFSource
        from visrag.sources.web import WebSource

        sources = [WebSource(), PDFSource(), LocalSource(), ImageSource()]
        for source in sources:
            if source.can_handle(document):
                return source
        raise ValueError(f"No source adapter for {document.source.value}: {document.path}")
