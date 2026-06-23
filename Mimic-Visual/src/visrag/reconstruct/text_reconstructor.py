"""Text reconstructor — SDM -> plain text."""

from __future__ import annotations

from visrag.core.chunk import Chunk
from visrag.reconstruct.base import AbstractReconstructor


class TextReconstructor(AbstractReconstructor):
    def reconstruct(self, chunks: list[Chunk], output_format: str = "text") -> str:
        parts = []
        for chunk in chunks:
            for block in chunk.blocks:
                prefix = ""
                if block.role == "heading":
                    prefix = "# "
                elif block.role == "list_item":
                    prefix = "- "
                elif block.role == "code":
                    prefix = "    "
                parts.append(f"{prefix}{block.text}")

            if chunk.tables:
                for table in chunk.tables:
                    grid: dict[tuple[int, int], str] = {}
                    for cell in table.cells:
                        grid[(cell.row, cell.col)] = cell.text
                    for r in range(table.row_count):
                        row_texts = [grid.get((r, c), "") for c in range(table.col_count)]
                        parts.append(" | ".join(row_texts))
                    parts.append("")

            parts.append("")
        return "\n".join(parts)

    @property
    def supported_formats(self) -> list[str]:
        return ["text"]
