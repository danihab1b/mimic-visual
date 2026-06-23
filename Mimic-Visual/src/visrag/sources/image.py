"""Image source adapter — reads standalone image files."""

from __future__ import annotations

from pathlib import Path

from visrag.core.document import Document, DocumentSource
from visrag.sources.base import AbstractSource

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif", ".webp"}


class ImageSource(AbstractSource):
    def can_handle(self, document: Document) -> bool:
        if document.source == DocumentSource.IMAGE:
            return True
        p = Path(document.path)
        return p.exists() and p.suffix.lower() in IMAGE_EXTENSIONS

    async def fetch_html(self, document: Document) -> str:
        return ""

    async def get_metadata(self, document: Document) -> dict:
        p = Path(document.path)
        meta = {"path": str(p), "source_type": "image"}
        if p.exists():
            meta["size_bytes"] = p.stat().st_size
            try:
                from PIL import Image
                img = Image.open(p)
                meta["width"], meta["height"] = img.size
                meta["format"] = img.format
                img.close()
            except Exception:
                pass
        return meta
