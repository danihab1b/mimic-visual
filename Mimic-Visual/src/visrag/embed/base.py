"""Abstract embedder interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from visrag.core.chunk import Chunk
from visrag.core.sdm import SDM


class AbstractEmbedder(ABC):
    @abstractmethod
    def embed_sdm(self, sdm: SDM) -> np.ndarray: ...

    @abstractmethod
    def embed_chunk(self, chunk: Chunk) -> np.ndarray: ...

    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray: ...

    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @staticmethod
    def create(model_type: str = "text-only", **kwargs) -> AbstractEmbedder:
        if model_type == "layout-aware":
            from visrag.embed.layout_aware import LayoutAwareEmbedder
            return LayoutAwareEmbedder(**kwargs)
        if model_type == "hybrid":
            from visrag.embed.hybrid import HybridEmbedder
            return HybridEmbedder(**kwargs)
        from visrag.embed.text_only import TextOnlyEmbedder
        return TextOnlyEmbedder(**kwargs)
