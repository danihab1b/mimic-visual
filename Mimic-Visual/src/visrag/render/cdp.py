"""CDP (Chrome DevTools Protocol) renderer — direct screenshot via CDP."""

from __future__ import annotations

import json
from pathlib import Path

from visrag.core.document import Document
from visrag.core.render import RenderResult, Tile
from visrag.render.base import AbstractRenderer


class CDPRenderer(AbstractRenderer):
    async def render(
        self,
        document: Document,
        output_dir: Path,
        viewport_width: int = 875,
        tile_height: int = 8192,
    ) -> RenderResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError("Playwright required for CDP renderer. pip install playwright")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": viewport_width, "height": 900})

            if document.source.value == "web":
                await page.goto(document.path, wait_until="networkidle", timeout=30000)
            elif document.path.endswith((".html", ".htm")):
                await page.goto(f"file://{Path(document.path).resolve()}", wait_until="networkidle")
            else:
                await browser.close()
                raise ValueError(f"CDP renderer cannot handle: {document.path}")

            await page.wait_for_timeout(1000)

            html_source = await page.content()
            (output_dir / "source.html").write_text(html_source, encoding="utf-8")

            page_height = await page.evaluate("() => document.documentElement.scrollHeight")
            tiles = []

            for idx in range(0, max(page_height, 1), tile_height):
                y = idx
                h = min(tile_height, page_height - y)
                if h <= 0:
                    break

                await page.evaluate(f"window.scrollTo(0, {y})")
                await page.wait_for_timeout(200)

                tile_path = output_dir / f"tile_{idx:04d}.jpg"
                await page.screenshot(path=str(tile_path), type="jpeg", quality=90)

                tile = Tile(
                    index=idx // tile_height,
                    y_offset=y,
                    width=viewport_width,
                    height=h,
                    file_path=str(tile_path),
                )
                tiles.append(tile)

            await browser.close()

        meta = {"url": document.path, "title": ""} if document.source.value == "web" else {}
        (output_dir / "source.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        tiles_manifest = {
            "page_width": viewport_width,
            "page_height": page_height,
            "tile_count": len(tiles),
            "tiles": [
                {"index": t.index, "y_offset": t.y_offset, "width": t.width, "height": t.height, "file_path": t.file_path}
                for t in tiles
            ],
        }
        (output_dir / "tiles.json").write_text(json.dumps(tiles_manifest, indent=2), encoding="utf-8")

        return RenderResult(
            document_id=document.id,
            page_width=viewport_width,
            page_height=page_height,
            tiles=tiles,
            html_source=html_source,
            metadata=meta,
        )
