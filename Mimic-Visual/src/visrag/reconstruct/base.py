"""Abstract reconstructor interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from visrag.core.chunk import Chunk


class AbstractReconstructor(ABC):
    @abstractmethod
    def reconstruct(self, chunks: list[Chunk], output_format: str) -> str: ...

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        return ["html", "svg", "text"]

    @staticmethod
    def create(format_name: str = "html", **kwargs) -> AbstractReconstructor:
        if format_name == "svg":
            from visrag.reconstruct.svg_reconstructor import SVGReconstructor
            return SVGReconstructor(**kwargs)
        if format_name == "text":
            from visrag.reconstruct.text_reconstructor import TextReconstructor
            return TextReconstructor(**kwargs)
        from visrag.reconstruct.html_reconstructor import HTMLReconstructor
        return HTMLReconstructor(**kwargs)
