"""Adapter for PaddleOCR — image -> text + quad boxes via PP-OCR.

PaddleOCR's constructor and ``ocr()`` signatures have shifted across major versions
(``use_angle_cls``/``cls`` in 2.x vs ``use_textline_orientation`` in 3.x), so this
adapter probes a couple of signatures defensively and parses the classic
``[[ [box, (text, score)], ... ]]`` result. Engines are cached per language.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """PaddleOCR adapter (caches one engine per language)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._engines: dict = {}

    def _engine(self, lang):
        if lang not in self._engines:
            from paddleocr import PaddleOCR

            try:
                self._engines[lang] = PaddleOCR(
                    use_angle_cls=True, lang=lang, show_log=False
                )
            except TypeError:
                # Newer PaddleOCR dropped/renamed those kwargs.
                self._engines[lang] = PaddleOCR(lang=lang)
        return self._engines[lang]

    def _read(self, image, *, lang="en", **extra) -> OcrResult:
        from ocracy.util import to_numpy

        arr = to_numpy(image)
        engine = self._engine(lang)
        try:
            raw = engine.ocr(arr, cls=True)
        except TypeError:
            raw = engine.ocr(arr)

        # Classic shape: raw is a per-image list; each page is a list of
        # [box, (text, score)] entries.
        page = raw[0] if raw and isinstance(raw, (list, tuple)) else raw
        blocks = []
        for item in page or []:
            try:
                box, (text, score) = item
            except (TypeError, ValueError):
                continue
            blocks.append(
                make_block(text, bbox=box, confidence=float(score), level="line")
            )

        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=raw)
