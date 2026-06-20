"""Adapter for Mistral OCR — image -> Markdown via the Mistral OCR API.

Mistral OCR is text/markdown-oriented (no per-word boxes or confidence): the
payload is per-page Markdown, joined into ``result.text`` and ``result.markdown``,
with the raw SDK response in ``result.raw``.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter


class Adapter(BaseOcrAdapter):
    """Mistral OCR API adapter."""

    def _read(self, image, *, model="mistral-ocr-latest", **extra) -> OcrResult:
        import base64

        from mistralai import Mistral

        from ocracy.credentials import resolve_credential
        from ocracy.util import load_image_bytes

        api_key = resolve_credential(
            "mistral-ocr",
            api_key=extra.pop("api_key", None),
            env_var=self.config.get("api_env_var"),
        )
        data = load_image_bytes(image)
        b64 = base64.b64encode(data).decode("ascii")

        client = Mistral(api_key=api_key)
        response = client.ocr.process(
            model=model,
            document={"type": "image_url", "image_url": f"data:image/png;base64,{b64}"},
        )

        pages = getattr(response, "pages", None) or []
        markdown = "\n\n".join((getattr(p, "markdown", "") or "") for p in pages)
        return OcrResult.from_text(
            markdown,
            backend=self.backend_id,
            raw=response,
            markdown=markdown,
            pages=len(pages),
        )
