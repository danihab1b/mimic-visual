"""Local file source adapter — reads HTML and image files from disk."""

from __future__ import annotations

from pathlib import Path

from visrag.core.document import Document, DocumentSource
from visrag.sources.base import AbstractSource


class LocalSource(AbstractSource):
    def can_handle(self, document: Document) -> bool:
        if document.source == DocumentSource.LOCAL:
            return True
        p = Path(document.path)
        return p.exists() and p.suffix.lower() in {".html", ".htm", ".xhtml", ".mhtml"}

    async def fetch_html(self, document: Document) -> str:
        p = Path(document.path)
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace")
        return ""

    async def get_metadata(self, document: Document) -> dict:
        p = Path(document.path)
        return {
            "path": str(p),
            "source_type": "local",
            "exists": p.exists(),
            "size_bytes": p.stat().st_size if p.exists() else 0,
        }
