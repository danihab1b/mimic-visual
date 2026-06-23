"""EasyOCR backend."""

from __future__ import annotations

from PIL import Image

from visrag.extract.ocr.base import AbstractOCREngine, OCRRegion


class EasyOCREngine(AbstractOCREngine):
    def __init__(self, language: str = "en", **kwargs):
        self.language = language
        self._reader = None

    def _load_model(self):
        if self._reader is not None:
            return
        try:
            import easyocr
            self._reader = easyocr.Reader([self.language])
        except ImportError:
            raise RuntimeError("easyocr required. pip install easyocr")

    def detect(self, image: Image.Image, language: str | None = None) -> list[OCRRegion]:
        self._load_model()
        import numpy as np
        img_array = np.array(image)
        results = self._reader.readtext(img_array)
        regions = []
        for order, (bbox_pts, text, conf) in enumerate(results):
            x1 = min(p[0] for p in bbox_pts)
            y1 = min(p[1] for p in bbox_pts)
            x2 = max(p[0] for p in bbox_pts)
            y2 = max(p[1] for p in bbox_pts)
            regions.append(OCRRegion(
                bbox=(float(x1), float(y1), float(x2), float(y2)),
                text=text,
                confidence=float(conf),
                reading_order=order,
            ))
        return regions

    def detect_batch(
        self,
        images: list[Image.Image],
        language: str | None = None,
        batch_size: int = 8,
    ) -> list[list[OCRRegion]]:
        return [self.detect(img, language) for img in images]

    @property
    def name(self) -> str:
        return "easyocr"
