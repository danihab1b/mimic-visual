"""Geometric chunker — fixed-height page slices."""

from __future__ import annotations

from visrag.chunk.base import AbstractChunker
from visrag.core.chunk import Chunk
from visrag.core.sdm import SDM


class GeometricChunker(AbstractChunker):
    def __init__(self, chunk_height: int = 1024, overlap_px: int = 0):
        self.chunk_height = chunk_height
        self.overlap_px = overlap_px

    def chunk(self, sdm: SDM, document_id: str) -> list[Chunk]:
        page_height = sdm.page_height
        if page_height <= 0:
            page_height = max(
                (b.bbox[3] for b in sdm.blocks),
                default=self.chunk_height,
            )

        chunks = []
        y = 0
        idx = 0

        while y < page_height:
            y_end = min(y + self.chunk_height, page_height)

            chunk_blocks = [b for b in sdm.blocks if _intersects(b.bbox, y, y_end)]
            chunk_tables = [t for t in sdm.tables if _intersects(t.bbox, y, y_end)]
            chunk_images = [i for i in sdm.images if _intersects(i.bbox, y, y_end)]

            if chunk_blocks or chunk_tables or chunk_images:
                chunk = Chunk(
                    chunk_id="",
                    document_id=document_id,
                    y_offset=y,
                    height=y_end - y,
                    blocks=chunk_blocks,
                    tables=chunk_tables,
                    images=chunk_images,
                )
                chunks.append(chunk)

            y = y_end - self.overlap_px if self.overlap_px > 0 else y_end
            if y >= page_height:
                break
            idx += 1

        return chunks


def _intersects(bbox: tuple, y_start: int, y_end: int) -> bool:
    _, b_y1, _, b_y3 = bbox
    return b_y1 < y_end and b_y3 > y_start
