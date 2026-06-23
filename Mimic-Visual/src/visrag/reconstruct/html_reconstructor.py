"""HTML reconstructor — SDM -> styled HTML."""

from __future__ import annotations

from visrag.core.chunk import Chunk
from visrag.reconstruct.base import AbstractReconstructor


class HTMLReconstructor(AbstractReconstructor):
    def __init__(self, inline_styles: bool = True, include_metadata: bool = True):
        self._inline_styles = inline_styles
        self._include_metadata = include_metadata

    def reconstruct(self, chunks: list[Chunk], output_format: str = "html") -> str:
        parts = [
            "<!DOCTYPE html>",
            '<html lang="en">',
            "<head>",
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            "<title>Reconstructed Document</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; }",
            ".chunk { margin-bottom: 20px; }",
            ".heading { font-size: 1.5em; font-weight: bold; margin: 10px 0; }",
            ".paragraph { margin: 8px 0; line-height: 1.6; }",
            ".code { font-family: monospace; background: #f5f5f5; padding: 12px; border-radius: 4px; }",
            ".list_item { margin-left: 20px; margin-bottom: 4px; }",
            ".table { border-collapse: collapse; margin: 12px 0; width: 100%; }",
            ".table th, .table td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            ".table th { background: #f5f5f5; font-weight: bold; }",
            ".caption { font-style: italic; color: #666; margin: 4px 0; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        if self._include_metadata and chunks:
            parts.append(f'<p style="color:#999;font-size:0.8em;">Document: {chunks[0].document_id}</p>')

        for chunk in chunks:
            parts.append(f'<div class="chunk" data-chunk-id="{chunk.chunk_id}" data-y-offset="{chunk.y_offset}">')

            for block in chunk.blocks:
                style = self._block_style(block) if self._inline_styles else ""
                tag = self._role_to_tag(block.role)
                cls = block.role if self._inline_styles else ""
                parts.append(f'<{tag} class="{cls}" style="{style}">{_escape(block.text)}</{tag}>')

            if chunk.tables:
                parts.append(self._render_tables(chunk))

            parts.append("</div>")

        parts.extend(["</body>", "</html>"])
        return "\n".join(parts)

    def _block_style(self, block) -> str:
        styles = []
        if block.font_size:
            styles.append(f"font-size:{block.font_size}px")
        if block.font_weight:
            styles.append(f"font-weight:{block.font_weight}")
        if block.text_align:
            styles.append(f"text-align:{block.text_align}")
        if block.bbox[0] > 0:
            styles.append(f"margin-left:{int(block.bbox[0])}px")
        return ";".join(styles)

    def _role_to_tag(self, role: str) -> str:
        return {
            "heading": "h2",
            "paragraph": "p",
            "list_item": "li",
            "code": "pre",
            "caption": "p",
            "table_cell": "td",
        }.get(role, "p")

    def _render_tables(self, chunk: Chunk) -> str:
        parts = []
        for table in chunk.tables:
            parts.append('<table class="table">')
            grid: dict[tuple[int, int], str] = {}
            for cell in table.cells:
                grid[(cell.row, cell.col)] = cell.text
            for r in range(table.row_count):
                parts.append("<tr>")
                for c in range(table.col_count):
                    tag = "th" if r == 0 else "td"
                    text = grid.get((r, c), "")
                    parts.append(f"<{tag}>{_escape(text)}</{tag}>")
                parts.append("</tr>")
            parts.append("</table>")
        return "\n".join(parts)

    @property
    def supported_formats(self) -> list[str]:
        return ["html"]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
