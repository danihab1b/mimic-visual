"""visrag index build / info."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

console = Console()


def run_index_build(input_dir: str, output_dir: str, config_path: str):
    from visrag.config.settings import VisRAGConfig
    config = VisRAGConfig.from_yaml(config_path)

    pages_path = Path(input_dir)
    page_dirs = sorted([d for d in pages_path.iterdir() if d.is_dir() and d.name.startswith("page_")])

    if not page_dirs:
        console.print("[red]No page directories found.[/]")
        return

    from visrag.chunk.geometric import GeometricChunker
    from visrag.embed.base import AbstractEmbedder
    from visrag.extract.sdm_builder import load_sdm
    from visrag.index.builder import IndexBuilder

    chunker = GeometricChunker(
        chunk_height=config.chunk.chunk_height,
        overlap_px=config.chunk.overlap_px,
    )
    embedder = AbstractEmbedder.create(config.embed.model, model_name=config.embed.model_name)
    builder = IndexBuilder(chunker, embedder, output_dir)

    sdms = {}
    doc_meta = {}
    for page_dir in page_dirs:
        extract_dir = pages_path / f"{page_dir.name}.extract"
        sdm_path = extract_dir / "sdm.json"
        if not sdm_path.exists():
            continue
        sdms[page_dir.name] = load_sdm(sdm_path)
        meta_path = page_dir / "source.meta.json"
        if meta_path.exists():
            doc_meta[page_dir.name] = json.loads(meta_path.read_text(encoding="utf-8"))

    console.print(f"[bold]Building index from {len(sdms)} documents...[/]")
    summary = builder.build_from_sdms(sdms, doc_meta)
    console.print(f"[green]Index built:[/] {summary['chunk_count']} chunks, dim={summary['dimension']}")


def run_index_info(index_dir: str):
    p = Path(index_dir)
    summary_path = p / "summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        console.print(f"[bold]Index: {index_dir}[/]")
        for k, v in summary.items():
            console.print(f"  {k}: {v}")
    else:
        console.print(f"[red]No summary.json found in {index_dir}[/]")
