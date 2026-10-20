"""Adapter for RapidOCR — image -> text + quad boxes via ONNXRuntime PP-OCR.

``rapidocr`` 3.x runs the same PP-OCRv6 models as PaddleOCR through ONNX, without
PaddlePaddle (measured in https://github.com/thorwhalen/ocracy/issues/22). Its
result is an object with ``boxes`` / ``txts`` / ``scores`` (all ``None`` when
nothing is found). The adapter builds the v6 pipeline at the requested ``lang`` and
``model_size`` (one engine cached per pair).

An install that only has the older ``rapidocr_onnxruntime`` package (PP-OCRv4,
which can drop word spaces) keeps working: the adapter falls back to it, ignores
``lang`` / ``model_size`` there (that package selects scripts itself).
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block

#: PP-OCRv6 is multilingual, so ``lang`` selects the recogniser's script set and
#: ``model_size`` the size of both detector and recogniser.
OCR_VERSION = "PP-OCRv6"


def is_v3_package() -> bool:
    """Whether the ``rapidocr`` 3.x package (not just the legacy one) is importable."""
    try:
        import rapidocr  # noqa: F401
    except ImportError:
        return False
    return True


def v6_params(lang: str, model_size: str) -> dict:
    """The ``RapidOCR(params=...)`` dict that selects PP-OCRv6 at ``lang`` and ``model_size``."""
    from rapidocr import ModelType, OCRVersion

    version, size = OCRVersion(OCR_VERSION), ModelType(model_size)
    return {
        "Det.ocr_version": version,
        "Det.model_type": size,
        "Rec.ocr_version": version,
        "Rec.model_type": size,
        "Rec.lang_type": lang,
    }


def blocks_from_v3(result) -> list:
    """Line blocks from a 3.x result object (``boxes`` / ``txts`` / ``scores``)."""
    if result is None or result.txts is None:
        return []
    scores = result.scores if result.scores is not None else [None] * len(result.txts)
    boxes = result.boxes if result.boxes is not None else [None] * len(result.txts)
    return [
        make_block(
            text,
            bbox=None if box is None else [tuple(map(float, p)) for p in box],
            confidence=None if score is None else float(score),
            level="line",
        )
        for box, text, score in zip(boxes, result.txts, scores)
    ]


def blocks_from_legacy(result) -> list:
    """Line blocks from ``rapidocr_onnxruntime``'s ``[[box, text, score], ...]`` (or ``None``)."""
    return [
        make_block(text, bbox=box, confidence=float(score), level="line")
        for box, text, score in (result or [])
    ]


class Adapter(BaseOcrAdapter):
    """RapidOCR adapter (caches one engine per ``(lang, model_size)``)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._engines: dict = {}

    def _engine(self, lang: str, model_size: str):
        key = (lang, model_size)
        if key not in self._engines:
            if is_v3_package():
                from rapidocr import RapidOCR

                self._engines[key] = RapidOCR(params=v6_params(lang, model_size))
            else:
                from rapidocr_onnxruntime import RapidOCR

                self._engines[key] = RapidOCR()
        return self._engines[key]

    def _read(self, image, *, lang="en", model_size="medium", **extra) -> OcrResult:
        from ocracy.util import to_numpy

        arr = to_numpy(image)
        engine = self._engine(lang, model_size)
        if is_v3_package():
            raw = engine(arr, **extra)
            return OcrResult.from_blocks(blocks_from_v3(raw), backend=self.backend_id, raw=raw)
        # Legacy: engine(img) -> (result, elapse).
        raw, _elapse = engine(arr, **extra)
        return OcrResult.from_blocks(blocks_from_legacy(raw), backend=self.backend_id, raw=raw)
