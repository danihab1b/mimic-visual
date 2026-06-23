"""visrag render — capture screenshots + HTML from documents."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console

console = Console()


def run_render(
    source: str,
    output_dir: str,
    engine: str | None,
    viewport_width: int,
    tile_height: int,
    config_path: str,
):
    from visrag.config.settings import VisRAGConfig
    config = VisRAGConfig.from_yaml(config_path)
    engine = engine or config.render.engine

    sources = _resolve_sources(source)
    console.print(f"[bold]Rendering {len(sources)} document(s) with {engine} engine[/]")

    for i, src in enumerate(sources):
        doc = _make_document(src)
        page_dir = Path(output_dir) / f"page_{i:03d}"
        console.print(f"  [{i+1}/{len(sources)}] {src} -> {page_dir}")

        from visrag.render.base import AbstractRenderer
        renderer = AbstractRenderer.create(engine)
        result = asyncio.get_event_loop().run_until_complete(
            renderer.render(doc, page_dir, viewport_width, tile_height)
        )
        console.print(f"    * {result.tile_count} tiles, {result.page_height}px tall")

    console.print(f"[green]Done.[/] Rendered to {output_dir}")


def _resolve_sources(source: str) -> list[str]:
    p = Path(source)
    if p.is_file() and p.suffix == ".txt":
        return [line.strip() for line in p.read_text().splitlines() if line.strip() and not line.startswith("#")]
    if p.is_dir():
        return [str(f) for f in p.iterdir() if f.suffix in {".html", ".htm", ".pdf", ".png", ".jpg"}]
    return [source]


def _make_document(source: str):
    from visrag.core.document import Document
    p = Path(source)
    if p.suffix == ".pdf":
        return Document.from_pdf(p)
    if p.suffix in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}:
        return Document.from_image(p)
    if p.suffix in {".html", ".htm"}:
        return Document.from_local(p)
    if source.startswith(("http://", "https://")):
        return Document.from_url(source)
    return Document.from_local(p)
