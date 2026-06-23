"""visrag reconstruct — rebuild HTML/SVG from a chunk ID."""

from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console

console = Console()


def run_reconstruct(chunk_id: str, output_format: str, index_dir: str, output: str | None):
    from visrag.index.metadata_store import MetadataStore

    store = MetadataStore(index_dir)
    chunk = store.load_chunk(chunk_id)

    if chunk is None:
        console.print(f"[red]Chunk {chunk_id} not found.[/]")
        sys.exit(1)

    from visrag.reconstruct.base import AbstractReconstructor
    reconstructor = AbstractReconstructor.create(output_format)
    result = reconstructor.reconstruct([chunk], output_format)

    if output:
        Path(output).write_text(result, encoding="utf-8")
        console.print(f"[green]Written to {output}[/]")
    else:
        console.print(result)
