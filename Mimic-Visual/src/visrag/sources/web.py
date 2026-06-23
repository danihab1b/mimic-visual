"""Web source adapter — fetches HTML from URLs."""

from __future__ import annotations

import httpx

from visrag.core.document import Document, DocumentSource
from visrag.sources.base import AbstractSource


class WebSource(AbstractSource):
    def can_handle(self, document: Document) -> bool:
        return document.source == DocumentSource.WEB

    async def fetch_html(self, document: Document) -> str:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(document.path)
            resp.raise_for_status()
            return resp.text

    async def get_metadata(self, document: Document) -> dict:
        return {"url": document.path, "source_type": "web"}
