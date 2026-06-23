"""Structured Document Model (SDM) and related types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from visrag.core.fusion import FusionBlock


@dataclass
class TableCell:
    text: str
    bbox: tuple[float, float, float, float]
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    is_header: bool = False
    provenance: str = "fused_high_conf"


@dataclass
class Table:
    cells: list[TableCell] = field(default_factory=list)
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    caption: str | None = None
    row_count: int = 0
    col_count: int = 0


@dataclass
class ImageRegion:
    bbox: tuple[float, float, float, float]
    alt_text: str | None = None
    caption: str | None = None
    src: str | None = None
    is_decoration: bool = False


@dataclass
class SDM:
    source_url: str
    page_width: int
    page_height: int
    blocks: list[FusionBlock] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    images: list[ImageRegion] = field(default_factory=list)
    layout_tree: dict | None = None
    language: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_url": self.source_url,
            "page_width": self.page_width,
            "page_height": self.page_height,
            "blocks": [b.to_dict() for b in self.blocks],
            "tables": [_table_to_dict(t) for t in self.tables],
            "images": [_image_to_dict(i) for i in self.images],
            "layout_tree": self.layout_tree,
            "language": self.language,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SDM:
        blocks = [FusionBlock.from_dict(b) for b in d.get("blocks", [])]
        tables = [_table_from_dict(t) for t in d.get("tables", [])]
        images = [_image_from_dict(i) for i in d.get("images", [])]
        return cls(
            source_url=d["source_url"],
            page_width=d["page_width"],
            page_height=d["page_height"],
            blocks=blocks,
            tables=tables,
            images=images,
            layout_tree=d.get("layout_tree"),
            language=d.get("language"),
            metadata=d.get("metadata", {}),
        )


def _table_to_dict(t: Table) -> dict:
    return {
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


def _table_from_dict(d: dict) -> Table:
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
        for c in d.get("cells", [])
    ]
    bbox = d.get("bbox", (0, 0, 0, 0))
    if isinstance(bbox, list):
        bbox = tuple(bbox)
    return Table(
        cells=cells,
        bbox=bbox,
        caption=d.get("caption"),
        row_count=d.get("row_count", 0),
        col_count=d.get("col_count", 0),
    )


def _image_to_dict(i: ImageRegion) -> dict:
    return {
        "bbox": list(i.bbox),
        "alt_text": i.alt_text,
        "caption": i.caption,
        "src": i.src,
        "is_decoration": i.is_decoration,
    }


def _image_from_dict(d: dict) -> ImageRegion:
    bbox = d.get("bbox", (0, 0, 0, 0))
    if isinstance(bbox, list):
        bbox = tuple(bbox)
    return ImageRegion(
        bbox=bbox,
        alt_text=d.get("alt_text"),
        caption=d.get("caption"),
        src=d.get("src"),
        is_decoration=d.get("is_decoration", False),
    )
