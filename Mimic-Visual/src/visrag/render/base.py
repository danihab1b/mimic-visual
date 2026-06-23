"""Abstract renderer interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from visrag.core.document import Document
from visrag.core.render import RenderResult


class AbstractRenderer(ABC):
    @abstractmethod
    async def render(
        self,
        document: Document,
        output_dir: Path,
        viewport_width: int = 875,
        tile_height: int = 8192,
    ) -> RenderResult: ...

    @staticmethod
    def create(engine: str = "cdp") -> AbstractRenderer:
        if engine == "playwright":
            from visrag.render.playwright import PlaywrightRenderer
            return PlaywrightRenderer()
        from visrag.render.cdp import CDPRenderer
        return CDPRenderer()
