"""visrag embed — encode chunks into vectors."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

console = Console()


def run_embed(pages_dir: str, model: str | None, model_name: str | None, config_path: str):
    from visrag.config.settings import VisRAGConfig
    config = VisRAGConfig.from_yaml(config_path)
    model = model or config.embed.model
    model_name = model_name or config.embed.model_name

    pages_path = Path(pages_dir)
    chunk_dirs = sorted([d for d in pages_path.iterdir() if d.is_dir() and d.name.endswith(".chunks")])

    if not chunk_dirs:
        console.print("[red]No .chunks directories found. Run 'visrag chunk' first.[/]")
        return

    import numpy as np

    from visrag.embed.base import AbstractEmbedder

    embedder = AbstractEmbedder.create(model, model_name=model_name)
    console.print(f"[bold]Embedding chunks with {embedder.name}[/]")

    for chunk_dir in chunk_dirs:
        chunks_json = chunk_dir / "chunks.json"
        if not chunks_json.exists():
            continue

        manifest = json.loads(chunks_json.read_text(encoding="utf-8"))
        embeddings = []

        for i, chunk_meta in enumerate(manifest["chunks"]):
            chunk_path = chunk_dir / f"chunk_{i:04d}.json"
            if not chunk_path.exists():
                continue

            chunk_data = json.loads(chunk_path.read_text(encoding="utf-8"))
            from visrag.core.chunk import Chunk
            chunk = Chunk.from_dict(chunk_data)

            emb = embedder.embed_chunk(chunk)
            embeddings.append(emb)

        if embeddings:
            emb_array = np.array(embeddings, dtype=np.float32)
            out_dir = pages_path / f"{chunk_dir.name.replace('.chunks', '')}.embeddings"
            out_dir.mkdir(parents=True, exist_ok=True)
            np.savez(out_dir / "embeddings.npz", embeddings=emb_array)
            (out_dir / "embedder_meta.json").write_text(
                json.dumps({"model": embedder.name, "dimension": embedder.dimension, "count": len(embeddings)}, indent=2),
                encoding="utf-8",
            )
            console.print(f"  {chunk_dir.name}: {len(embeddings)} embeddings")

    console.print("[green]Done.[/]")
