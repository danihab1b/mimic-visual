"""SDM builder — assembles FusionBlocks into a Structured Document Model."""

from __future__ import annotations

import json
from pathlib import Path

from visrag.core.sdm import SDM, ImageRegion
from visrag.extract.fusion_engine import FusionConfig, fuse_html_and_ocr
from visrag.extract.html_parser import extract_text_nodes
from visrag.extract.layout_analyzer import analyze_layout
from visrag.extract.ocr.base import AbstractOCREngine, OCRRegion
from visrag.extract.table_detector import detect_tables


def build_sdm(
    ocr_regions: list[OCRRegion],
    html_source: str,
    page_width: int,
    page_height: int,
    source_url: str = "",
    fusion_config: FusionConfig | None = None,
    do_table_detection: bool = True,
    do_layout_analysis: bool = True,
) -> SDM:
    """Build a Structured Document Model from OCR results and HTML source."""
    html_nodes = extract_text_nodes(html_source) if html_source.strip() else []
    ocr_text = "\n".join(r.text for r in ocr_regions)
    ocr_bboxes = [r.bbox for r in ocr_regions]
    ocr_confidences = [r.confidence for r in ocr_regions]

    blocks = fuse_html_and_ocr(
        html_nodes=html_nodes,
        ocr_text=ocr_text,
        ocr_bboxes=ocr_bboxes,
        ocr_confidences=ocr_confidences,
        page_width=page_width,
        page_height=page_height,
        config=fusion_config,
    )

    if do_layout_analysis:
        blocks = analyze_layout(blocks)

    tables = detect_tables(blocks, page_width, page_height) if do_table_detection else []

    table_block_positions = set()
    for table in tables:
        for cell in table.cells:
            for i, block in enumerate(blocks):
                if block.bbox == cell.bbox:
                    table_block_positions.add(i)

    filtered_blocks = [b for i, b in enumerate(blocks) if i not in table_block_positions]

    images = _detect_images(html_source, page_width, page_height)

    return SDM(
        source_url=source_url,
        page_width=page_width,
        page_height=page_height,
        blocks=filtered_blocks,
        tables=tables,
        images=images,
        metadata={
            "html_node_count": len(html_nodes),
            "ocr_region_count": len(ocr_regions),
            "fusion_block_count": len(filtered_blocks),
            "table_count": len(tables),
        },
    )


def build_sdm_from_tiles(
    tile_paths: list[str],
    ocr_engine: AbstractOCREngine,
    html_source: str,
    page_width: int,
    page_height: int,
    source_url: str = "",
    fusion_config: FusionConfig | None = None,
) -> SDM:
    """Build SDM from tile images + OCR engine + HTML source."""
    from PIL import Image

    all_regions: list[OCRRegion] = []
    for path in tile_paths:
        img = Image.open(path)
        regions = ocr_engine.detect(img)
        y_offset = _get_tile_y_offset(path)
        shifted = [
            OCRRegion(
                bbox=(r.bbox[0], r.bbox[1] + y_offset, r.bbox[2], r.bbox[3] + y_offset),
                text=r.text,
                confidence=r.confidence,
                reading_order=r.reading_order,
                is_table=r.is_table,
            )
            for r in regions
        ]
        all_regions.extend(shifted)

    all_regions.sort(key=lambda r: (r.bbox[1], r.bbox[0]))
    for i, r in enumerate(all_regions):
        r.reading_order = i

    return build_sdm(
        ocr_regions=all_regions,
        html_source=html_source,
        page_width=page_width,
        page_height=page_height,
        source_url=source_url,
        fusion_config=fusion_config,
    )


def _get_tile_y_offset(path: str) -> int:
    import re
    match = re.search(r"tile_(\d+)", Path(path).stem)
    if match:
        return int(match.group(1))
    return 0


def _detect_images(html_source: str, page_width: int, page_height: int) -> list[ImageRegion]:
    images = []
    if not html_source:
        return images
    try:
        from lxml import html as lxml_html
        doc = lxml_html.document_fromstring(html_source)
        for img in doc.xpath("//img"):
            src = img.get("src", "")
            alt = img.get("alt", "")
            x = float(img.get("x", 0) or 0)
            y = float(img.get("y", 0) or 0)
            w = float(img.get("width", 100) or 100)
            h = float(img.get("height", 100) or 100)
            is_decoration = not alt.strip() and w * h < 10000
            images.append(ImageRegion(
                bbox=(x, y, x + w, y + h),
                alt_text=alt if alt.strip() else None,
                src=src,
                is_decoration=is_decoration,
            ))
    except Exception:
        pass
    return images


def save_sdm(sdm: SDM, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(sdm.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def load_sdm(path: Path) -> SDM:
    data = json.loads(path.read_text(encoding="utf-8"))
    return SDM.from_dict(data)
