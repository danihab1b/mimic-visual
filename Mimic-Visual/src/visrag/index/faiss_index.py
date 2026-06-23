"""FAISS index implementation."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from visrag.index.base import AbstractIndex


class FAISSIndex(AbstractIndex):
    def __init__(self, dimension: int, metric: str = "cosine", nlist: int = 128):
        self._dimension = dimension
        self._metric = metric
        self._nlist = nlist
        self._index = None
        self._chunk_ids: list[str] = []

    def _init_index(self):
        if self._index is not None:
            return
        try:
            import faiss
        except ImportError:
            raise RuntimeError("faiss-cpu required. pip install faiss-cpu")

        if self._metric == "cosine" or self._metric == "ip":
            if self._chunk_ids is not None and len(self._chunk_ids) < self._nlist * 4:
                self._index = faiss.IndexFlatIP(self._dimension)
            else:
                quantizer = faiss.IndexFlatIP(self._dimension)
                self._index = faiss.IndexIVFFlat(quantizer, self._dimension, self._nlist, faiss.METRIC_INNER_PRODUCT)
        else:
            if self._chunk_ids is not None and len(self._chunk_ids) < self._nlist * 4:
                self._index = faiss.IndexFlatL2(self._dimension)
            else:
                quantizer = faiss.IndexFlatL2(self._dimension)
                self._index = faiss.IndexIVFFlat(quantizer, self._dimension, self._nlist, faiss.METRIC_L2)

    def add(self, chunk_ids: list[str], embeddings: np.ndarray):
        self._init_index()
        self._chunk_ids.extend(chunk_ids)
        vecs = embeddings.astype(np.float32)
        if self._metric in ("cosine", "ip"):
            norms = np.linalg.norm(vecs, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            vecs = vecs / norms
        if hasattr(self._index, "train") and not self._index.is_trained:
            self._index.train(vecs)
        self._index.add(vecs)

    def search(self, query_embedding: np.ndarray, n_results: int) -> list[tuple[str, float]]:
        self._init_index()
        if self._index.ntotal == 0:
            return []
        q = query_embedding.astype(np.float32).reshape(1, -1)
        if self._metric in ("cosine", "ip"):
            norms = np.linalg.norm(q, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            q = q / norms
        n_results = min(n_results, self._index.ntotal)
        distances, indices = self._index.search(q, n_results)
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self._chunk_ids):
                continue
            score = float(dist) if self._metric in ("cosine", "ip") else float(1.0 / (1.0 + dist))
            results.append((self._chunk_ids[idx], score))
        return results

    def save(self, path: str):
        import faiss
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(p / "index.faiss"))
        (p / "chunk_ids.json").write_text(json.dumps(self._chunk_ids), encoding="utf-8")

    def load(self, path: str):
        import faiss
        p = Path(path)
        index_file = p / "index.faiss"
        chunk_ids_file = p / "chunk_ids.json"
        if not index_file.exists():
            self._init_index()
            return
        self._index = faiss.read_index(str(index_file))
        if chunk_ids_file.exists():
            self._chunk_ids = json.loads(chunk_ids_file.read_text(encoding="utf-8"))
        else:
            self._chunk_ids = []
        self._dimension = self._index.d

    @property
    def size(self) -> int:
        if self._index is None:
            return 0
        return self._index.ntotal
