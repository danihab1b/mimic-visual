"""Fusion engine — orchestrates HTML + OCR -> FusionBlocks."""

from __future__ import annotations

from dataclasses import dataclass

from visrag.core.fusion import FusionBlock, ProvenanceType
from visrag.extract.aligner import alignment_quality, needleman_wunsch_align
from visrag.extract.html_parser import HTMLTextNode


@dataclass
class FusionConfig:
    match_bonus: int = 2
    mismatch_penalty: int = -1
    gap_penalty: int = -1
    html_confidence_bonus: float = 0.1


def fuse_html_and_ocr(
    html_nodes: list[HTMLTextNode],
    ocr_text: str,
    ocr_bboxes: list[tuple[float, float, float, float]],
    ocr_confidences: list[float],
    page_width: int,
    page_height: int,
    config: FusionConfig | None = None,
) -> list[FusionBlock]:
    """Fuse HTML text nodes with OCR results into FusionBlocks."""
    cfg = config or FusionConfig()

    html_text = "".join(n.text for n in html_nodes)
    if not html_text.strip() and not ocr_text.strip():
        return []

    if not ocr_text.strip():
        return _html_only_blocks(html_nodes, page_width, page_height)

    if not html_text.strip():
        return _ocr_only_blocks(ocr_text, ocr_bboxes, ocr_confidences)

    alignment = needleman_wunsch_align(
        html_text, ocr_text,
        match_bonus=cfg.match_bonus,
        mismatch_penalty=cfg.mismatch_penalty,
        gap_penalty=cfg.gap_penalty,
    )
    quality = alignment_quality(alignment)
    html_conf = quality + cfg.html_confidence_bonus

    blocks = _build_fused_blocks(alignment, html_nodes, ocr_text, ocr_bboxes, ocr_confidences, quality, cfg)

    blocks.sort(key=lambda b: (b.bbox[1], b.bbox[0]))
    return blocks


def _build_fused_blocks(
    alignment,
    html_nodes: list[HTMLTextNode],
    ocr_text: str,
    ocr_bboxes: list[tuple[float, float, float, float]],
    ocr_confidences: list[float],
    quality: float,
    config: FusionConfig,
) -> list[FusionBlock]:
    blocks = []
    html_chars = list("".join(n.text for n in html_nodes))
    html_pos_to_node = _map_html_positions(html_nodes)

    aligned_html = alignment.aligned_html
    aligned_ocr = alignment.aligned_ocr

    html_run_start = None
    ocr_run_start = None
    html_run_chars = []
    ocr_run_chars = []

    for pos in range(len(aligned_html)):
        h_char = aligned_html[pos]
        o_char = aligned_ocr[pos]

        is_match = h_char == o_char and h_char != "-"
        is_html_gap = h_char == "-" and o_char != "-"
        is_ocr_gap = h_char != "-" and o_char == "-"
        is_mismatch = h_char != "-" and o_char != "-" and h_char != o_char

        if is_match or is_mismatch:
            if html_run_start is None:
                html_run_start = pos
                ocr_run_start = pos
                html_run_chars = []
                ocr_run_chars = []
            html_run_chars.append(h_char)
            ocr_run_chars.append(o_char)
        else:
            if html_run_chars:
                block = _create_block_from_run(
                    html_run_chars, ocr_run_chars,
                    html_run_start, ocr_run_start,
                    html_pos_to_node, ocr_bboxes, ocr_confidences,
                    quality, config, is_mismatch=False,
                )
                if block:
                    blocks.append(block)
                html_run_start = None
                ocr_run_start = None
                html_run_chars = []
                ocr_run_chars = []

            if is_html_gap:
                node_idx = alignment.ocr_indices[pos]
                bbox = ocr_bboxes[node_idx] if node_idx is not None and node_idx < len(ocr_bboxes) else (0, 0, 100, 20)
                conf = ocr_confidences[node_idx] if node_idx is not None and node_idx < len(ocr_confidences) else 0.5
                blocks.append(FusionBlock(
                    text=o_char,
                    bbox=bbox,
                    provenance="ocr",
                    ocr_text=o_char,
                    ocr_confidence=conf,
                    is_embedded_image_text=True,
                    role="other",
                ))

    if html_run_chars:
        block = _create_block_from_run(
            html_run_chars, ocr_run_chars,
            html_run_start, ocr_run_start,
            html_pos_to_node, ocr_bboxes, ocr_confidences,
            quality, config, is_mismatch=False,
        )
        if block:
            blocks.append(block)

    return blocks


def _create_block_from_run(
    html_chars: list[str],
    ocr_chars: list[str],
    html_start: int | None,
    ocr_start: int | None,
    html_pos_to_node: dict[int, HTMLTextNode],
    ocr_bboxes: list[tuple[float, float, float, float]],
    ocr_confidences: list[float],
    quality: float,
    config: FusionConfig,
    is_mismatch: bool,
) -> FusionBlock | None:
    html_text = "".join(html_chars).strip()
    ocr_text = "".join(ocr_chars).strip()
    if not html_text and not ocr_text:
        return None

    best_text = html_text if html_text else ocr_text
    provenance: ProvenanceType = "fused_high_conf" if quality > 0.7 and not is_mismatch else "fused_low_conf"

    bbox = (0, 0, 100, 20)
    ocr_conf = 0.5
    if ocr_start is not None and ocr_start < len(ocr_bboxes):
        bbox = ocr_bboxes[ocr_start]
    if ocr_start is not None and ocr_start < len(ocr_confidences):
        ocr_conf = ocr_confidences[ocr_start]

    node = html_pos_to_node.get(html_start) if html_start is not None else None
    html_conf = quality + config.html_confidence_bonus

    if is_mismatch:
        best_text, _ = _resolve_conflict(html_text, ocr_text, html_conf, ocr_conf)

    return FusionBlock(
        text=best_text,
        bbox=bbox,
        provenance=provenance,
        html_text=html_text if html_text else None,
        ocr_text=ocr_text if ocr_text else None,
        html_confidence=html_conf,
        ocr_confidence=ocr_conf,
        role="other",
        font_size=node.font_size if node else None,
        font_weight=node.font_weight if node else None,
        text_align=node.text_align if node else None,
        is_embedded_image_text=False,
        xpath=node.xpath if node else None,
        dom_depth=node.dom_depth if node else None,
    )


def _resolve_conflict(html_text: str, ocr_text: str, html_conf: float, ocr_conf: float) -> tuple[str, float]:
    if html_text.lower() in ocr_text.lower():
        return ocr_text, max(html_conf, ocr_conf)
    if ocr_text.lower() in html_text.lower():
        return html_text, max(html_conf, ocr_conf)
    if html_conf > ocr_conf + 0.2:
        return html_text, html_conf
    if ocr_conf > html_conf + 0.2:
        return ocr_text, ocr_conf
    return html_text, (html_conf + ocr_conf) / 2


def _html_only_blocks(html_nodes: list[HTMLTextNode], page_width: int, page_height: int) -> list[FusionBlock]:
    blocks = []
    for i, node in enumerate(html_nodes):
        text = node.text.strip()
        if not text:
            continue
        y_est = min(i * 20, page_height - 20)
        w_est = min(len(text) * 8, page_width)
        blocks.append(FusionBlock(
            text=text,
            bbox=(0, y_est, w_est, y_est + 20),
            provenance="html",
            html_text=text,
            html_confidence=0.9,
            role=_tag_to_role(node.tag_name),
            font_size=node.font_size,
            font_weight=node.font_weight,
            text_align=node.text_align,
            xpath=node.xpath,
            dom_depth=node.dom_depth,
        ))
    return blocks


def _ocr_only_blocks(ocr_text: str, bboxes: list[tuple], confidences: list[float]) -> list[FusionBlock]:
    blocks = []
    lines = ocr_text.split("\n")
    for i, line in enumerate(lines):
        text = line.strip()
        if not text:
            continue
        bbox = bboxes[i] if i < len(bboxes) else (0, i * 20, 300, i * 20 + 20)
        conf = confidences[i] if i < len(confidences) else 0.5
        blocks.append(FusionBlock(
            text=text,
            bbox=bbox,
            provenance="ocr",
            ocr_text=text,
            ocr_confidence=conf,
            is_embedded_image_text=True,
            role="other",
        ))
    return blocks


def _map_html_positions(nodes: list[HTMLTextNode]) -> dict[int, HTMLTextNode]:
    mapping = {}
    pos = 0
    for node in nodes:
        for _ in node.text:
            mapping[pos] = node
            pos += 1
    return mapping


def _tag_to_role(tag: str) -> str:
    tag = tag.lower()
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return "heading"
    if tag in ("p",):
        return "paragraph"
    if tag in ("li",):
        return "list_item"
    if tag in ("ul", "ol"):
        return "list"
    if tag in ("td", "th"):
        return "table_cell"
    if tag in ("caption", "figcaption"):
        return "caption"
    if tag in ("code", "pre"):
        return "code"
    if tag in ("img",):
        return "image_alt"
    return "other"
