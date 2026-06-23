"""Layout analyzer — role classification for FusionBlocks."""

from __future__ import annotations

import re

from visrag.core.fusion import FusionBlock, RoleType

HEADING_PATTERN = re.compile(r"^(#{1,6})\s|^(.+)\n[=\-]{3,}$")


def analyze_layout(blocks: list[FusionBlock]) -> list[FusionBlock]:
    """Assign roles to blocks based on text patterns and DOM metadata."""
    for block in blocks:
        if block.role != "other":
            continue
        block.role = _classify_role(block)
    return blocks


def _classify_role(block: FusionBlock) -> RoleType:
    if block.dom_depth is not None and block.dom_depth <= 3:
        tag = (block.xpath or "").split("/")[-1].lower() if block.xpath else ""
        if tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            return "heading"

    text = block.text.strip()

    if block.font_size and block.font_size >= 20:
        return "heading"
    if block.font_weight == "bold" and len(text) < 100:
        return "heading"

    if HEADING_PATTERN.match(text):
        return "heading"

    if text.startswith(("```", "    ", "\t")) or re.match(r"^\w+\s*[=\(]", text):
        return "code"

    if re.match(r"^[\-\*\•]\s", text) or re.match(r"^\d+[\.\)]\s", text):
        return "list_item"

    if text.startswith(("http://", "https://", "www.")):
        return "paragraph"

    if block.is_embedded_image_text:
        return "caption"

    return "paragraph"
