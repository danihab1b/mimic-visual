"""POST /reconstruct route."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from visrag.reconstruct.base import AbstractReconstructor

router = APIRouter()


class ReconstructRequest(BaseModel):
    chunk_ids: list[str]
    format: str = "html"
    options: dict = {}


@router.post("/reconstruct")
async def reconstruct(request: Request, body: ReconstructRequest):
    store = request.app.state.store
    reconstructor: AbstractReconstructor | None = request.app.state.reconstructor

    if reconstructor is None:
        from visrag.reconstruct.html_reconstructor import HTMLReconstructor
        reconstructor = HTMLReconstructor()

    chunks = []
    for cid in body.chunk_ids:
        chunk = store.load_chunk(cid)
        if chunk:
            chunks.append(chunk)

    if not chunks:
        return {"format": body.format, "content": "", "chunk_count": 0, "coverage_px": 0}

    content = reconstructor.reconstruct(chunks, body.format)
    total_height = sum(c.height for c in chunks)

    return {
        "format": body.format,
        "content": content,
        "chunk_count": len(chunks),
        "coverage_px": total_height,
    }
