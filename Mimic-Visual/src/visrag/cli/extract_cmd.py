"""visrag extract — OCR -> align -> fuse -> build SDM."""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console

console = Console()


def run_extract(
    pages_dir: str,
    ocr_engine_name: str | None,
    language: str | None,
    config_path: str,
):
    from visrag.config.settings import VisRAGConfig
    config = VisRAGConfig.from_yaml(config_path)

    ocr_engine_name = ocr_engine_name or config.extract.ocr.engine
    language = language or config.extract.ocr.language

    pages_path = Path(pages_dir)
    page_dirs = sorted([d for d in pages_path.iterdir() if d.is_dir() and d.name.startswith("page_")])

    if not page_dirs:
        console.print("[red]No page directories found.[/]")
        return

    console.print(f"[bold]Extracting {len(page_dirs)} pages with {ocr_engine_name} OCR[/]")

    from visrag.extract.fusion_engine import FusionConfig
    from visrag.extract.ocr.base import AbstractOCREngine
    from visrag.extract.sdm_builder import build_sdm_from_tiles, save_sdm

    ocr = AbstractOCREngine.create(ocr_engine_name)
    fusion_config = FusionConfig(
        match_bonus=config.extract.alignment.match_bonus,
        mismatch_penalty=config.extract.alignment.mismatch_penalty,
        gap_penalty=config.extract.alignment.gap_penalty,
        html_confidence_bonus=config.extract.alignment.html_confidence_bonus,
    )

    for page_dir in page_dirs:
        console.print(f"  Processing {page_dir.name}...")

        tiles_json = page_dir / "tiles.json"
        if not tiles_json.exists():
            console.print("    [yellow]Skipping — no tiles.json[/]")
            continue

        manifest = json.loads(tiles_json.read_text(encoding="utf-8"))
        tile_paths = [t["file_path"] for t in manifest["tiles"]]
        page_width = manifest["page_width"]
        page_height = manifest["page_height"]

        html_path = page_dir / "source.html"
        html_source = html_path.read_text(encoding="utf-8") if html_path.exists() else ""

        sdm = build_sdm_from_tiles(
            tile_paths=tile_paths,
            ocr_engine=ocr,
            html_source=html_source,
            page_width=page_width,
            page_height=page_height,
            fusion_config=fusion_config,
        )

        extract_dir = pages_path / f"{page_dir.name}.extract"
        save_sdm(sdm, extract_dir / "sdm.json")

        provenance_stats = {}
        for b in sdm.blocks:
            provenance_stats[b.provenance] = provenance_stats.get(b.provenance, 0) + 1
        (extract_dir / "fusion_report.json").write_text(
            json.dumps({"provenance_counts": provenance_stats, "block_count": len(sdm.blocks)}, indent=2),
            encoding="utf-8",
        )

        console.print(f"    * {len(sdm.blocks)} blocks, {len(sdm.tables)} tables")

    console.print(f"[green]Done.[/] SDMs saved to {pages_dir}")
