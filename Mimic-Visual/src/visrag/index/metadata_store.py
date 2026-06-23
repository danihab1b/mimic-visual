"""Sidecar metadata store — chunk_id -> SDM + metadata."""

from __future__ import annotations

import json
from pathlib import Path

from visrag.core.chunk import Chunk


class MetadataStore:
    def __init__(self, base_dir: str | Path):
        self._dir = Path(base_dir) / "metadata_store"
        self._dir.mkdir(parents=True, exist_ok=True)

    def save_chunk(self, chunk: Chunk):
        path = self._dir / f"{chunk.chunk_id}.json"
        path.write_text(json.dumps(chunk.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")

    def load_chunk(self, chunk_id: str) -> Chunk | None:
        path = self._dir / f"{chunk_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Chunk.from_dict(data)

    def has_chunk(self, chunk_id: str) -> bool:
        return (self._dir / f"{chunk_id}.json").exists()

    def list_chunks(self) -> list[str]:
        return [p.stem for p in self._dir.glob("*.json")]

    def save_document_metadata(self, document_id: str, metadata: dict):
        path = self._dir / f"doc_{document_id}.json"
        path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_document_metadata(self, document_id: str) -> dict | None:
        path = self._dir / f"doc_{document_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
