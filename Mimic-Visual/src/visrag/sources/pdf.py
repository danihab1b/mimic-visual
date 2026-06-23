"""PDF source adapter — extracts text/images from PDF files."""

from __future__ import annotations

from pathlib import Path

from visrag.core.document import Document, DocumentSource
from visrag.sources.base import AbstractSource


class PDFSource(AbstractSource):
    def can_handle(self, document: Document) -> bool:
        if document.source == DocumentSource.PDF:
            return True
        return Path(document.path).suffix.lower() == ".pdf"

    async def fetch_html(self, document: Document) -> str:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(document.path)
            html_parts = []
            for page in doc:
                text = page.get_text("text")
                if text.strip():
                    html_parts.append(f"<div class='page'>{text}</div>")
            doc.close()
            return "\n".join(html_parts)
        except ImportError:
            return ""

    async def get_metadata(self, document: Document) -> dict:
        meta = {"path": document.path, "source_type": "pdf"}
        try:
            import fitz
            doc = fitz.open(document.path)
            meta["page_count"] = doc.page_count
            meta["title"] = doc.metadata.get("title", "")
            doc.close()
        except Exception:
            pass
        return meta
