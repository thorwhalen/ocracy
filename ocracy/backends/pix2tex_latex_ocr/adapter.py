"""Adapter for pix2tex — image of an equation -> LaTeX, locally.

Math OCR is text-oriented: the LaTeX string is ``result.text``, also surfaced as
``result.markdown`` (``$$…$$``) and ``result.meta['latex']``. The model is heavy to
construct, so it is built once and cached.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter


class Adapter(BaseOcrAdapter):
    """pix2tex (LaTeX-OCR) adapter (caches the model)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._model = None

    def _get_model(self):
        if self._model is None:
            from pix2tex.cli import LatexOCR

            self._model = LatexOCR()
        return self._model

    def _read(self, image, **extra) -> OcrResult:
        from ocracy.util import to_pil

        pil = to_pil(image).convert("RGB")
        latex = self._get_model()(pil)
        return OcrResult.from_text(
            latex,
            backend=self.backend_id,
            raw=latex,
            markdown=f"$$\n{latex}\n$$",
            latex=latex,
        )
