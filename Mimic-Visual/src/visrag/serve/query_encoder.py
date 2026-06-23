"""Query -> embedding encoder."""

from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image

from visrag.embed.base import AbstractEmbedder


class QueryEncoder:
    def __init__(self, embedder: AbstractEmbedder):
        self._embedder = embedder

    def encode(self, text: str | None = None, image_b64: str | None = None) -> np.ndarray:
        if text:
            return self._embedder.embed_query(text)
        if image_b64:
            img_data = base64.b64decode(image_b64)
            img = Image.open(io.BytesIO(img_data))
            return self._embedder.embed_query(img)
        raise ValueError("Either text or image must be provided")
