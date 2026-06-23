"""Index builder — orchestrates chunking + embedding + indexing."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visrag.chunk.base import AbstractChunker
from visrag.core.chunk import Chunk
from visrag.core.sdm import SDM
from visrag.embed.base import AbstractEmbedder
from visrag.index.faiss_index import FAISSIndex
from visrag.index.metadata_store import MetadataStore


class IndexBuilder:
    def __init__(
        self,
        chunker: AbstractChunker,
        embedder: AbstractEmbedder,
        output_dir: str | Path,
    ):
        self._chunker = chunker
        self._embedder = embedder
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def build_from_sdms(self, sdms: dict[str, SDM], document_metadata: dict[str, dict] | None = None) -> dict[str, Any]:
        all_chunks: list[Chunk] = []
        for doc_id, sdm in sdms.items():
            chunks = self._chunker.chunk(sdm, doc_id)
            all_chunks.extend(chunks)

        return self._build_index(all_chunks, document_metadata or {})

    def build_from_page_dirs(self, page_dirs: list[str]) -> dict[str, Any]:
        from visrag.extract.sdm_builder import load_sdm

        sdms: dict[str, SDM] = {}
        doc_metadata: dict[str, dict] = {}

        for page_dir in page_dirs:
            p = Path(page_dir)
            sdm_path = p.parent / f"{p.name}.extract" / "sdm.json"
            if not sdm_path.exists():
                continue
            sdm = load_sdm(sdm_path)
            doc_id = p.name
            sdms[doc_id] = sdm

            meta_path = p / "source.meta.json"
            if meta_path.exists():
                doc_metadata[doc_id] = json.loads(meta_path.read_text(encoding="utf-8"))

        return self.build_from_sdms(sdms, doc_metadata)

    def _build_index(self, chunks: list[Chunk], document_metadata: dict[str, dict]) -> dict[str, Any]:
        store = MetadataStore(self._output_dir)

        texts = [c.text_content for c in chunks]
        if not texts:
            return {"chunk_count": 0, "dimension": 0}

        embeddings = self._embedder.embed_query("dummy")
        dim = len(embeddings)

        all_embeddings = np.zeros((len(chunks), dim), dtype=np.float32)
        for i, chunk in enumerate(chunks):
            emb = self._embedder.embed_chunk(chunk)
            all_embeddings[i] = emb
            chunk.embedding = None
            store.save_chunk(chunk)

        for doc_id, meta in document_metadata.items():
            store.save_document_metadata(doc_id, meta)

        index = FAISSIndex(dimension=dim)
        chunk_ids = [c.chunk_id for c in chunks]
        index.add(chunk_ids, all_embeddings)
        index.save(str(self._output_dir))

        summary = {
            "chunk_count": len(chunks),
            "dimension": dim,
            "embedder": self._embedder.name,
            "document_count": len(document_metadata),
        }
        (self._output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

        return summary
