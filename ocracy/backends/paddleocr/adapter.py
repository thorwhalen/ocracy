"""Adapter for PaddleOCR — image -> text + quad boxes via PP-OCR.

PaddleOCR 3.x replaced the 2.x API: the constructor refuses 2.x keywords such as
``show_log``, ``predict()`` returns result objects holding ``rec_texts`` /
``rec_scores`` / ``rec_polys`` instead of 2.x ``ocr()``'s ``[[box, (text, score)],
...]``, and language names changed (3.x takes ISO codes). The adapter tells the two
apart by whether ``PaddleOCR`` has ``predict`` (2.x accepts any keyword, so a
constructor error cannot), then builds and parses accordingly. The 3.x document
pre-processors (page orientation, unwarping, text-line orientation) are off: they
are for photographed pages, and they slow every call. Engines are cached per
language.
"""

from ocracy.backends.paddleocr.config import V2_LANG, V3_LANG
from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block

# 3.x pipeline switches that only help photographed or rotated pages.
V3_PREPROCESSORS_OFF = {
    "use_doc_orientation_classify": False,
    "use_doc_unwarping": False,
    "use_textline_orientation": False,
}


def is_v3(paddle_class) -> bool:
    """Whether a PaddleOCR pipeline class has the 3.x API (``predict``)."""
    return callable(getattr(paddle_class, "predict", None))


def blocks_from_v3(page) -> list:
    """Line blocks from one 3.x result (``rec_texts`` / ``rec_scores`` / ``rec_polys``)."""
    texts = page.get("rec_texts") or []
    scores = page.get("rec_scores") or [None] * len(texts)
    polys = page.get("rec_polys")
    if polys is None:
        polys = [None] * len(texts)
    return [
        make_block(
            text,
            bbox=[tuple(map(float, p)) for p in poly] if poly is not None else None,
            confidence=None if score is None else float(score),
            level="line",
        )
        for text, score, poly in zip(texts, scores, polys)
    ]


def blocks_from_v2(page) -> list:
    """Line blocks from one 2.x page (``[[box, (text, score)], ...]``)."""
    blocks = []
    for item in page or []:
        try:
            box, (text, score) = item
        except (TypeError, ValueError):
            continue
        blocks.append(make_block(text, bbox=box, confidence=float(score), level="line"))
    return blocks


class Adapter(BaseOcrAdapter):
    """PaddleOCR adapter (caches one engine per language)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._engines: dict = {}

    def _engine(self, lang):
        if lang not in self._engines:
            from paddleocr import PaddleOCR

            if is_v3(PaddleOCR):
                native = V3_LANG.get(lang, lang)
                engine = PaddleOCR(lang=native, **V3_PREPROCESSORS_OFF)
            else:
                native = V2_LANG.get(lang, lang)
                engine = PaddleOCR(use_angle_cls=True, lang=native, show_log=False)
            self._engines[lang] = (engine, is_v3(PaddleOCR))
        return self._engines[lang]

    def _read(self, image, *, lang="en", **extra) -> OcrResult:
        from ocracy.util import to_numpy

        arr = to_numpy(image)
        engine, v3 = self._engine(lang)
        if v3:
            raw = engine.predict(arr, **extra)
            blocks = blocks_from_v3(raw[0]) if raw else []
        else:
            raw = engine.ocr(arr, cls=True, **extra)
            page = raw[0] if raw and isinstance(raw, (list, tuple)) else raw
            blocks = blocks_from_v2(page)
        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=raw)
