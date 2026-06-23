"""Chunk — a page slice of the SDM."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

from visrag.core.fusion import FusionBlock
from visrag.core.sdm import ImageRegion, Table


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    y_offset: int
    height: int
    blocks: list[FusionBlock] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    images: list[ImageRegion] = field(default_factory=list)
    embedding: Any = None

    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = self._generate_id()

    def _generate_id(self) -> str:
        content = f"{self.document_id}:{self.y_offset}:{self.height}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    @property
    def text_content(self) -> str:
        return "\n".join(b.text for b in self.blocks if b.text.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "y_offset": self.y_offset,
            "height": self.height,
            "blocks": [b.to_dict() for b in self.blocks],
            "tables": [
                {
                    "cells": [
                        {
                            "text": c.text,
                            "bbox": list(c.bbox),
                            "row": c.row,
                            "col": c.col,
                            "rowspan": c.rowspan,
                            "colspan": c.colspan,
                            "is_header": c.is_header,
                            "provenance": c.provenance,
                        }
                        for c in t.cells
                    ],
                    "bbox": list(t.bbox),
                    "caption": t.caption,
                    "row_count": t.row_count,
                    "col_count": t.col_count,
                }
                for t in self.tables
            ],
            "images": [
                {
                    "bbox": list(i.bbox),
                    "alt_text": i.alt_text,
                    "caption": i.caption,
                    "src": i.src,
                    "is_decoration": i.is_decoration,
                }
                for i in self.images
            ],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Chunk:
        from visrag.core.fusion import FusionBlock
        from visrag.core.sdm import ImageRegion, Table, TableCell

        blocks = [FusionBlock.from_dict(b) for b in d.get("blocks", [])]
        tables = []
        for t in d.get("tables", []):
            cells = [
                TableCell(
                    text=c["text"],
                    bbox=tuple(c["bbox"]) if isinstance(c["bbox"], list) else c["bbox"],
                    row=c["row"],
                    col=c["col"],
                    rowspan=c.get("rowspan", 1),
                    colspan=c.get("colspan", 1),
                    is_header=c.get("is_header", False),
                    provenance=c.get("provenance", "fused_high_conf"),
                )
                for c in t.get("cells", [])
            ]
            bbox = t.get("bbox", (0, 0, 0, 0))
            if isinstance(bbox, list):
                bbox = tuple(bbox)
            tables.append(Table(
                cells=cells,
                bbox=bbox,
                caption=t.get("caption"),
                row_count=t.get("row_count", 0),
                col_count=t.get("col_count", 0),
            ))
        images = [
            ImageRegion(
                bbox=tuple(i["bbox"]) if isinstance(i["bbox"], list) else i["bbox"],
                alt_text=i.get("alt_text"),
                caption=i.get("caption"),
                src=i.get("src"),
                is_decoration=i.get("is_decoration", False),
            )
            for i in d.get("images", [])
        ]
        return cls(
            chunk_id=d["chunk_id"],
            document_id=d["document_id"],
            y_offset=d["y_offset"],
            height=d["height"],
            blocks=blocks,
            tables=tables,
            images=images,
        )
