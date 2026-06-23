"""Render result and tile primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Tile:
    index: int
    y_offset: int
    width: int
    height: int
    file_path: str
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)

    def __post_init__(self):
        self.bbox = (0.0, float(self.y_offset), float(self.width), float(self.y_offset + self.height))


@dataclass
class RenderResult:
    document_id: str
    page_width: int
    page_height: int
    tiles: list[Tile] = field(default_factory=list)
    html_source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def tile_count(self) -> int:
        return len(self.tiles)

    def get_tile_paths(self) -> list[str]:
        return [t.file_path for t in self.tiles]
