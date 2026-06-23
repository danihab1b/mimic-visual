"""Abstract OCR engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from PIL import Image


@dataclass
class OCRRegion:
    bbox: tuple[float, float, float, float]  # x1, y1, x2, y2
    text: str
    confidence: float
    reading_order: int | None = None
    is_table: bool | None = None


class AbstractOCREngine(ABC):
    @abstractmethod
    def detect(
        self,
        image: Image.Image,
        language: str | None = None,
    ) -> list[OCRRegion]: ...

    @abstractmethod
    def detect_batch(
        self,
        images: list[Image.Image],
        language: str | None = None,
        batch_size: int = 8,
    ) -> list[list[OCRRegion]]: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @staticmethod
    def create(engine_name: str = "surya", **kwargs) -> AbstractOCREngine:
        if engine_name == "doctr":
            from visrag.extract.ocr.doctr import DocTROCREngine
            return DocTROCREngine(**kwargs)
        if engine_name == "easyocr":
            from visrag.extract.ocr.easyocr import EasyOCREngine
            return EasyOCREngine(**kwargs)
        from visrag.extract.ocr.surya import SuryaOCREngine
        return SuryaOCREngine(**kwargs)
