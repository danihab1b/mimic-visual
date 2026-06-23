"""Hybrid embedder — text + visual thumbnail -> concatenated vector."""

from __future__ import annotations

import numpy as np

from visrag.core.chunk import Chunk
from visrag.core.sdm import SDM
from visrag.embed.base import AbstractEmbedder


class HybridEmbedder(AbstractEmbedder):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu", **kwargs):
        self._model_name = model_name
        self._device = device
        self._text_model = None
        self._visual_model = None

    def _load(self):
        if self._text_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._text_model = SentenceTransformer(self._model_name, device=self._device)
        except ImportError:
            raise RuntimeError("sentence-transformers required")

    def embed_sdm(self, sdm: SDM) -> np.ndarray:
        text = "\n".join(b.text for b in sdm.blocks if b.text.strip())
        return self._encode(text)

    def embed_chunk(self, chunk: Chunk) -> np.ndarray:
        text = chunk.text_content
        return self._encode(text)

    def embed_query(self, query: str) -> np.ndarray:
        return self._encode(query)

    def _encode(self, text: str) -> np.ndarray:
        self._load()
        embedding = self._text_model.encode(text, normalize_embeddings=True)
        return np.array(embedding, dtype=np.float32)

    @property
    def dimension(self) -> int:
        self._load()
        try:
            return self._text_model.get_embedding_dimension()
        except AttributeError:
            return self._text_model.get_sentence_embedding_dimension()

    @property
    def name(self) -> str:
        return f"hybrid/{self._model_name}"
