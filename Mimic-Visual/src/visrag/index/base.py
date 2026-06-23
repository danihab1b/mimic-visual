"""Abstract index interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class AbstractIndex(ABC):
    @abstractmethod
    def add(self, chunk_ids: list[str], embeddings: np.ndarray): ...

    @abstractmethod
    def search(self, query_embedding: np.ndarray, n_results: int) -> list[tuple[str, float]]: ...

    @abstractmethod
    def save(self, path: str): ...

    @abstractmethod
    def load(self, path: str): ...

    @property
    @abstractmethod
    def size(self) -> int: ...
