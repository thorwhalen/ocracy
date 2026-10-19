"""Adapter for PaddleOCR PP-StructureV3 — image -> Markdown with tables, plus text lines.

``result.markdown`` is the document as PP-StructureV3 renders it: headings and
paragraphs as Markdown, tables as HTML, formulas as LaTeX. ``result.blocks`` are
the PP-OCR text lines it found along the way (``level="line"``), so ``result.lines``
works as with ``paddleocr``; ``result.text`` joins those lines.

PP-StructureV3 needs PaddleOCR's ``doc-parser`` extra on top of ``paddleocr``. When
it is missing, PaddleOCR raises a ``RuntimeError`` at construction; the adapter
turns that into an ``ImportError`` that names the install line.
"""

from ocracy.backends.paddleocr.adapter import V3_PREPROCESSORS_OFF, blocks_from_v3
from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter

_INSTALL = 'pip install "ocracy[paddleocr-ppstructure]"'


class Adapter(BaseOcrAdapter):
    """PP-StructureV3 adapter (caches one pipeline per language)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._pipelines: dict = {}

    def _pipeline(self, lang):
        if lang not in self._pipelines:
            try:
                from paddleocr import PPStructureV3
            except ImportError as e:  # paddleocr 2.x, or not installed
                raise ImportError(
                    f"paddleocr-ppstructure needs PaddleOCR 3.x with its doc-parser "
                    f"extra: {_INSTALL}"
                ) from e
            try:
                self._pipelines[lang] = PPStructureV3(lang=lang, **V3_PREPROCESSORS_OFF)
            except RuntimeError as e:  # paddlex's DependencyError, re-raised
                raise ImportError(
                    f"PP-StructureV3 is missing dependencies ({e}). Install them: {_INSTALL}"
                ) from e
        return self._pipelines[lang]

    def _read(self, image, *, lang="en", **extra) -> OcrResult:
        from ocracy.util import to_numpy

        raw = self._pipeline(lang).predict(to_numpy(image), **extra)
        page = raw[0] if raw else None
        if page is None:
            return OcrResult.from_blocks([], backend=self.backend_id, raw=raw)
        blocks = blocks_from_v3(page.get("overall_ocr_res") or {})
        markdown = page.markdown
        if isinstance(markdown, dict):
            markdown = markdown.get("markdown_texts", "")
        return OcrResult.from_blocks(
            blocks, backend=self.backend_id, raw=raw, markdown=(markdown or "").strip()
        )
