"""Layout-aware embedder — text + position tokens -> small transformer."""

from __future__ import annotations

import numpy as np

from visrag.core.chunk import Chunk
from visrag.core.sdm import SDM
from visrag.embed.base import AbstractEmbedder


class LayoutAwareEmbedder(AbstractEmbedder):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu", **kwargs):
        self._model_name = model_name
        self._device = device
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name, device=self._device)
        except ImportError:
            raise RuntimeError("sentence-transformers required")

    def embed_sdm(self, sdm: SDM) -> np.ndarray:
        text = self._sdm_to_text(sdm)
        return self._encode(text)

    def embed_chunk(self, chunk: Chunk) -> np.ndarray:
        text = self._chunk_to_text(chunk)
        return self._encode(text)

    def embed_query(self, query: str) -> np.ndarray:
        return self._encode(query)

    def _sdm_to_text(self, sdm: SDM) -> str:
        parts = []
        for b in sdm.blocks:
            role_tag = f"[{b.role}]" if b.role != "other" else ""
            parts.append(f"{role_tag} {b.text}")
        return "\n".join(parts)

    def _chunk_to_text(self, chunk: Chunk) -> str:
        parts = []
        for b in chunk.blocks:
            role_tag = f"[{b.role}]" if b.role != "other" else ""
            parts.append(f"{role_tag} {b.text}")
        return "\n".join(parts)

    def _encode(self, text: str) -> np.ndarray:
        self._load()
        embedding = self._model.encode(text, normalize_embeddings=True)
        return np.array(embedding, dtype=np.float32)

    @property
    def dimension(self) -> int:
        self._load()
        try:
            return self._model.get_embedding_dimension()
        except AttributeError:
            return self._model.get_sentence_embedding_dimension()

    @property
    def name(self) -> str:
        return f"layout-aware/{self._model_name}"
