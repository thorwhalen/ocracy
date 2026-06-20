"""Adapter for RapidOCR — image -> text + quad boxes via ONNXRuntime PP-OCR."""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """RapidOCR adapter (lazily builds and caches one engine)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._engine = None

    def _get_engine(self):
        if self._engine is None:
            from rapidocr_onnxruntime import RapidOCR

            self._engine = RapidOCR()
        return self._engine

    def _read(self, image, **extra) -> OcrResult:
        from ocracy.util import to_numpy

        arr = to_numpy(image)
        # engine(img) -> (result, elapse); result is a list of [box, text, score]
        # (or None when nothing is found).
        result, _elapse = self._get_engine()(arr, **extra)
        blocks = [
            make_block(text, bbox=box, confidence=float(score), level="line")
            for box, text, score in (result or [])
        ]
        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=result)
