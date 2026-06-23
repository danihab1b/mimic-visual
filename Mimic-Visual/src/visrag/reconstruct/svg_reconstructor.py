"""SVG reconstructor — SDM -> SVG layout."""

from __future__ import annotations

from visrag.core.chunk import Chunk
from visrag.reconstruct.base import AbstractReconstructor


class SVGReconstructor(AbstractReconstructor):
    def reconstruct(self, chunks: list[Chunk], output_format: str = "svg") -> str:
        max_width = max((c.blocks[-1].bbox[2] if c.blocks else 800) for c in chunks) if chunks else 800
        max_height = max((c.y_offset + c.height) for c in chunks) if chunks else 600

        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int(max_width)} {int(max_height)}">',
            '<style>text { font-family: sans-serif; }</style>',
        ]

        for chunk in chunks:
            for block in chunk.blocks:
                x, y = block.bbox[0], block.bbox[1]
                font_size = block.font_size or 14
                weight = block.font_weight or "normal"
                fill = "#000" if block.role != "caption" else "#666"
                parts.append(
                    f'<text x="{x}" y="{y + font_size}" font-size="{font_size}" '
                    f'font-weight="{weight}" fill="{fill}">{_escape(block.text)}</text>'
                )

            for table in chunk.tables:
                for cell in table.cells:
                    x, y, x2, y2 = cell.bbox
                    parts.append(f'<rect x="{x}" y="{y}" width="{x2-x}" height="{y2-y}" fill="none" stroke="#ccc"/>')
                    parts.append(f'<text x="{x+4}" y="{y+16}" font-size="12">{_escape(cell.text)}</text>')

        parts.append("</svg>")
        return "\n".join(parts)

    @property
    def supported_formats(self) -> list[str]:
        return ["svg"]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
