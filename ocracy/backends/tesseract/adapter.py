"""Adapter for Tesseract — image -> text+word-boxes via pytesseract.

A worked example of the adapter contract:

1. Normalize the input to a PIL image (``ocracy.util.to_pil``).
2. Call the engine *inside* ``_read`` (lazy import of ``pytesseract``).
3. Map Tesseract's TSV-style word rows into normalized ``TextBlock``s (boxes +
   confidence rescaled 0..100 -> 0..1) and assemble reading-order text, keeping
   the raw dict in ``raw=``.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


def _assemble_text(data: dict) -> str:
    """Join Tesseract word rows into reading-order text (words by space, lines by \\n)."""
    lines: dict = {}
    order: list = []
    for i, txt in enumerate(data["text"]):
        if not txt or not txt.strip():
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if key not in lines:
            lines[key] = []
            order.append(key)
        lines[key].append(txt)
    return "\n".join(" ".join(lines[k]) for k in order)


class Adapter(BaseOcrAdapter):
    """Tesseract adapter."""

    def _read(
        self, image, *, lang=None, psm=None, oem=None, config="", **extra
    ) -> OcrResult:
        import pytesseract
        from pytesseract import Output

        from ocracy.util import to_pil

        cfg_parts = []
        if psm is not None:
            cfg_parts.append(f"--psm {psm}")
        if oem is not None:
            cfg_parts.append(f"--oem {oem}")
        if config:
            cfg_parts.append(config)
        cfg = " ".join(cfg_parts)

        pil = to_pil(image)
        call_kwargs = {"config": cfg}
        if lang:
            call_kwargs["lang"] = lang

        data = pytesseract.image_to_data(pil, output_type=Output.DICT, **call_kwargs)

        blocks = []
        for i, txt in enumerate(data["text"]):
            if not txt or not txt.strip():
                continue
            try:
                conf = float(data["conf"][i])
            except (TypeError, ValueError):
                conf = -1.0
            if conf < 0:  # -1 marks non-text rows
                continue
            x, y = data["left"][i], data["top"][i]
            w, h = data["width"][i], data["height"][i]
            blocks.append(
                make_block(
                    txt,
                    bbox=(x, y, x + w, y + h),
                    confidence=conf,
                    conf_scale=100,
                    level="word",
                    block=data["block_num"][i],
                    paragraph=data["par_num"][i],
                    line=data["line_num"][i],
                )
            )

        return OcrResult.from_blocks(
            blocks,
            backend=self.backend_id,
            raw=data,
            text=_assemble_text(data),
            engine="tesseract",
        )
