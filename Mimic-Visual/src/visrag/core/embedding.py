"""Embedding vector typed wrapper."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class EmbeddingVector:
    vector: np.ndarray
    dimension: int

    def __post_init__(self):
        if self.vector.ndim != 1:
            self.vector = self.vector.flatten()
        self.dimension = len(self.vector)

    def normalize(self) -> EmbeddingVector:
        norm = np.linalg.norm(self.vector)
        if norm > 0:
            self.vector = self.vector / norm
        return self

    def to_list(self) -> list[float]:
        return self.vector.tolist()

    @classmethod
    def from_list(cls, values: list[float]) -> EmbeddingVector:
        return cls(vector=np.array(values, dtype=np.float32), dimension=len(values))
