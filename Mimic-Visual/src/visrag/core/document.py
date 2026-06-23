"""Document and source type primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DocumentSource(str, Enum):
    WEB = "web"
    PDF = "pdf"
    LOCAL = "local"
    IMAGE = "image"


@dataclass
class Document:
    source: DocumentSource
    path: str
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        import hashlib
        content = f"{self.source.value}:{self.path}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @classmethod
    def from_url(cls, url: str, **kwargs: Any) -> Document:
        return cls(source=DocumentSource.WEB, path=url, **kwargs)

    @classmethod
    def from_pdf(cls, path: str | Path, **kwargs: Any) -> Document:
        return cls(source=DocumentSource.PDF, path=str(path), **kwargs)

    @classmethod
    def from_local(cls, path: str | Path, **kwargs: Any) -> Document:
        return cls(source=DocumentSource.LOCAL, path=str(path), **kwargs)

    @classmethod
    def from_image(cls, path: str | Path, **kwargs: Any) -> Document:
        return cls(source=DocumentSource.IMAGE, path=str(path), **kwargs)
