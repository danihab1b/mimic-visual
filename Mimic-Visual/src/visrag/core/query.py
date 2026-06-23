"""Search query and result primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from visrag.core.chunk import Chunk


@dataclass
class SearchQuery:
    text: str | None = None
    image: str | None = None  # base64-encoded image
    n_results: int = 10
    include_sdm: bool = True


@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    document_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "document_id": self.chunk.document_id,
            "score": self.score,
            "y_offset": self.chunk.y_offset,
            "height": self.chunk.height,
            "sdm": self.chunk.to_dict() if self.document_metadata.get("include_sdm") else None,
            "document_metadata": self.document_metadata,
        }
