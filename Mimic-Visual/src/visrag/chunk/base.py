"""Abstract chunker interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from visrag.core.chunk import Chunk
from visrag.core.sdm import SDM


class AbstractChunker(ABC):
    @abstractmethod
    def chunk(self, sdm: SDM, document_id: str) -> list[Chunk]: ...

    @staticmethod
    def create(strategy: str = "geometric", **kwargs) -> AbstractChunker:
        if strategy == "semantic":
            from visrag.chunk.geometric import GeometricChunker
            return GeometricChunker(**kwargs)
        from visrag.chunk.geometric import GeometricChunker
        return GeometricChunker(**kwargs)
