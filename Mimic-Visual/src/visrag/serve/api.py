"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from visrag.embed.base import AbstractEmbedder
from visrag.index.faiss_index import FAISSIndex
from visrag.index.metadata_store import MetadataStore
from visrag.reconstruct.base import AbstractReconstructor


def create_app(
    index_dir: str,
    embedder: AbstractEmbedder,
    reconstructor: AbstractReconstructor | None = None,
    max_results: int = 20,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    app = FastAPI(title="Mimic-Visual", version="0.1.0")

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    index = FAISSIndex(dimension=embedder.dimension)
    index.load(index_dir)
    store = MetadataStore(index_dir)

    app.state.index = index
    app.state.embedder = embedder
    app.state.store = store
    app.state.reconstructor = reconstructor
    app.state.max_results = max_results
    app.state.index_dir = index_dir

    from visrag.serve.routes.reconstruct import router as reconstruct_router
    from visrag.serve.routes.search import router as search_router
    from visrag.serve.routes.status import router as status_router

    app.include_router(search_router)
    app.include_router(reconstruct_router)
    app.include_router(status_router)

    return app
