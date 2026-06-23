"""Embedder registry."""

from __future__ import annotations

from visrag.embed.base import AbstractEmbedder

_REGISTRY: dict[str, type[AbstractEmbedder]] = {}


def register_embedder(name: str, cls: type[AbstractEmbedder]):
    _REGISTRY[name] = cls


def get_embedder(name: str, **kwargs) -> AbstractEmbedder:
    if name in _REGISTRY:
        return _REGISTRY[name](**kwargs)
    return AbstractEmbedder.create(name, **kwargs)
