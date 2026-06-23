"""DocTR OCR backend."""

from __future__ import annotations

from PIL import Image

from visrag.extract.ocr.base import AbstractOCREngine, OCRRegion


class DocTROCREngine(AbstractOCREngine):
    def __init__(self, **kwargs):
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from doctr.models import ocr_predictor
            self._model = ocr_predictor(pretrained=True)
        except ImportError:
            raise RuntimeError("python-doctr required. pip install python-doctr")

    def detect(self, image: Image.Image, language: str | None = None) -> list[OCRRegion]:
        self._load_model()
        import numpy as np
        img_array = np.array(image)
        result = self._model([img_array])
        regions = []
        order = 0
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    text = " ".join(w.value for w in line.words)
                    bbox = line.geometry
                    x1, y1 = bbox[0]
                    x2, y2 = bbox[2]
                    regions.append(OCRRegion(
                        bbox=(x1 * image.width, y1 * image.height, x2 * image.width, y2 * image.height),
                        text=text,
                        confidence=line.confidence if hasattr(line, "confidence") else 0.9,
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
        return [self.detect(img, language) for img in images]

    @property
    def name(self) -> str:
        return "doctr"
