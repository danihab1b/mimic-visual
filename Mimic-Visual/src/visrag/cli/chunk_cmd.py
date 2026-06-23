"""visrag chunk — split SDMs into fixed-height slices."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

console = Console()


def run_chunk(pages_dir: str, height: int, overlap: int, config_path: str):
    from visrag.config.settings import VisRAGConfig
    config = VisRAGConfig.from_yaml(config_path)
    height = height or config.chunk.chunk_height

    pages_path = Path(pages_dir)
    extract_dirs = sorted([d for d in pages_path.iterdir() if d.is_dir() and d.name.endswith(".extract")])

    if not extract_dirs:
        console.print("[red]No .extract directories found. Run 'visrag extract' first.[/]")
        return

    from visrag.chunk.geometric import GeometricChunker
    from visrag.extract.sdm_builder import load_sdm

    chunker = GeometricChunker(chunk_height=height, overlap_px=overlap)
    console.print(f"[bold]Chunking {len(extract_dirs)} SDMs (height={height}px)[/]")

    for extract_dir in extract_dirs:
        sdm_path = extract_dir / "sdm.json"
        if not sdm_path.exists():
            continue

        sdm = load_sdm(sdm_path)
        doc_id = extract_dir.name.replace(".extract", "")
        chunks = chunker.chunk(sdm, doc_id)

        chunk_dir = pages_path / f"{doc_id}.chunks"
        chunk_dir.mkdir(parents=True, exist_ok=True)

        manifest = {"chunk_count": len(chunks), "chunks": []}
        for i, chunk in enumerate(chunks):
            chunk_path = chunk_dir / f"chunk_{i:04d}.json"
            chunk_path.write_text(json.dumps(chunk.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
            manifest["chunks"].append({"chunk_id": chunk.chunk_id, "y_offset": chunk.y_offset, "height": chunk.height})

        (chunk_dir / "chunks.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        console.print(f"  {doc_id}: {len(chunks)} chunks")

    console.print("[green]Done.[/]")
