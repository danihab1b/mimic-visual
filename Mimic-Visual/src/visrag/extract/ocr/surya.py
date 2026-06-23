"""Surya OCR backend."""

from __future__ import annotations

from PIL import Image

from visrag.extract.ocr.base import AbstractOCREngine, OCRRegion


class SuryaOCREngine(AbstractOCREngine):
    def __init__(self, language: str = "auto", batch_size: int = 4):
        self.language = language
        self.batch_size = batch_size
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from surya.recognition import RecognitionPredictor
            self._model = RecognitionPredictor()
        except ImportError:
            raise RuntimeError("surya-ocr required. pip install surya-ocr")

    def detect(self, image: Image.Image, language: str | None = None) -> list[OCRRegion]:
        self._load_model()
        lang = language or self.language
        predictions = self._model([image], langs=[[lang]] if lang != "auto" else None)
        regions = []
        order = 0
        for pred in predictions:
            for text_line in pred:
                regions.append(OCRRegion(
                    bbox=tuple(text_line.bbox),
                    text=text_line.text,
                    confidence=text_line.confidence,
                    reading_order=order,
                ))
                order += 1
        return regions

    def detect_batch(
        self,
        images: list[Image.Image],
        language: str | None = None,
        batch_size: int = 8,
    ) -> list[list[OCRRegion]]:
        self._load_model()
        lang = language or self.language
        predictions = self._model(images, langs=[[lang] for _ in images] if lang != "auto" else None)
        results = []
        for pred in predictions:
            regions = []
            order = 0
            for text_line in pred:
                regions.append(OCRRegion(
                    bbox=tuple(text_line.bbox),
                    text=text_line.text,
                    confidence=text_line.confidence,
                    reading_order=order,
                ))
                order += 1
            results.append(regions)
        return results

    @property
    def name(self) -> str:
        return "surya"
