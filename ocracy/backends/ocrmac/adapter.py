"""Adapter for ocrmac — image -> text via the macOS Vision framework.

Vision reports bounding boxes as normalized ``(x, y, w, h)`` with a bottom-left
origin; this adapter converts them to ocracy's pixel, top-left convention using
the image's pixel size.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """Apple Vision adapter (macOS only)."""

    def _read(
        self, image, *, language_preference=None, recognition_level="accurate", **extra
    ) -> OcrResult:
        from ocrmac import ocrmac

        from ocracy.util import to_pil

        pil = to_pil(image).convert("RGB")
        width, height = pil.size

        kwargs = {"recognition_level": recognition_level}
        if language_preference:
            kwargs["language_preference"] = language_preference

        # recognize() -> list of (text, confidence, (x, y, w, h)) with normalized,
        # bottom-left-origin boxes.
        annotations = ocrmac.OCR(pil, **kwargs).recognize()

        blocks = []
        for text, conf, (x, y, w, h) in annotations:
            x0 = x * width
            x1 = (x + w) * width
            y0 = (1.0 - (y + h)) * height  # flip to top-left origin
            y1 = (1.0 - y) * height
            blocks.append(
                make_block(
                    text, bbox=(x0, y0, x1, y1), confidence=float(conf), level="line"
                )
            )

        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=annotations)
