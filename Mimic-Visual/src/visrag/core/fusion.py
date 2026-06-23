"""FusionBlock and provenance primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProvenanceType = Literal[
    "fused_high_conf",
    "fused_low_conf",
    "html",
    "ocr",
]

RoleType = Literal[
    "heading", "paragraph", "list", "list_item",
    "table_cell", "image_alt", "caption", "code", "other",
]

FontWeightType = Literal["normal", "bold", "lighter", "bolder"]
TextAlignType = Literal["left", "center", "right", "justify"]


@dataclass
class FusionBlock:
    text: str
    bbox: tuple[float, float, float, float]
    provenance: ProvenanceType
    html_text: str | None = None
    ocr_text: str | None = None
    html_confidence: float | None = None
    ocr_confidence: float | None = None
    role: RoleType = "other"
    font_size: float | None = None
    font_weight: FontWeightType | None = None
    text_align: TextAlignType | None = None
    is_embedded_image_text: bool = False
    xpath: str | None = None
    dom_depth: int | None = None

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "bbox": list(self.bbox),
            "provenance": self.provenance,
            "html_text": self.html_text,
            "ocr_text": self.ocr_text,
            "html_confidence": self.html_confidence,
            "ocr_confidence": self.ocr_confidence,
            "role": self.role,
            "font_size": self.font_size,
            "font_weight": self.font_weight,
            "text_align": self.text_align,
            "is_embedded_image_text": self.is_embedded_image_text,
            "xpath": self.xpath,
            "dom_depth": self.dom_depth,
        }

    @classmethod
    def from_dict(cls, d: dict) -> FusionBlock:
        bbox = d.get("bbox", (0, 0, 0, 0))
        if isinstance(bbox, list):
            bbox = tuple(bbox)
        return cls(
            text=d["text"],
            bbox=bbox,
            provenance=d["provenance"],
            html_text=d.get("html_text"),
            ocr_text=d.get("ocr_text"),
            html_confidence=d.get("html_confidence"),
            ocr_confidence=d.get("ocr_confidence"),
            role=d.get("role", "other"),
            font_size=d.get("font_size"),
            font_weight=d.get("font_weight"),
            text_align=d.get("text_align"),
            is_embedded_image_text=d.get("is_embedded_image_text", False),
            xpath=d.get("xpath"),
            dom_depth=d.get("dom_depth"),
        )
