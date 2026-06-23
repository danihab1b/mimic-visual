"""POST /search route."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel

from visrag.serve.query_encoder import QueryEncoder

router = APIRouter()


class SearchRequest(BaseModel):
    text: str | None = None
    image: str | None = None
    n_results: int = 10
    include_sdm: bool = True


@router.post("/search")
async def search(request: Request, body: SearchRequest):
    embedder = request.app.state.embedder
    index = request.app.state.index
    store = request.app.state.store

    encoder = QueryEncoder(embedder)
    query_emb = encoder.encode(text=body.text, image_b64=body.image)

    raw_results = index.search(query_emb, body.n_results)

    results = []
    for chunk_id, score in raw_results:
        chunk = store.load_chunk(chunk_id)
        if chunk is None:
            continue
        doc_meta = store.load_document_metadata(chunk.document_id) or {}
        doc_meta["include_sdm"] = body.include_sdm
        results.append({
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "score": score,
            "y_offset": chunk.y_offset,
            "height": chunk.height,
            "sdm": chunk.to_dict() if body.include_sdm else None,
            "document_metadata": doc_meta,
        })

    return {"results": results, "query_time_ms": 0}
