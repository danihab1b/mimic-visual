"""GET /health route."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

router = APIRouter()
_start_time = time.time()


@router.get("/health")
async def health(request: Request):
    index = request.app.state.index
    embedder = request.app.state.embedder
    return {
        "status": "ok",
        "index_size": index.size,
        "embedder": embedder.name,
        "index_dimension": embedder.dimension,
        "uptime_seconds": int(time.time() - _start_time),
    }
