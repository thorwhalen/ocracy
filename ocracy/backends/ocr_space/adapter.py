"""Adapter for OCR.space — image -> text + word boxes via its REST API."""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block

_ENDPOINT = "https://api.ocr.space/parse/image"


class Adapter(BaseOcrAdapter):
    """OCR.space REST adapter."""

    def _read(
        self, image, *, language="eng", isOverlayRequired=True, **extra
    ) -> OcrResult:
        # Resolve credentials first (cheap, dependency-free) so a missing key fails
        # fast with guidance before we import/network.
        from ocracy.credentials import resolve_credential

        api_key = resolve_credential(
            "ocr-space",
            api_key=extra.pop("api_key", None),
            env_var=self.config.get("api_env_var"),
        )

        import requests

        from ocracy.util import is_url, load_image_bytes

        payload = {
            "apikey": api_key,
            "language": language,
            "isOverlayRequired": isOverlayRequired,
        }
        payload.update({k: v for k, v in extra.items() if v is not None})

        if is_url(image):
            payload["url"] = image
            resp = requests.post(_ENDPOINT, data=payload, timeout=60)
        else:
            data = load_image_bytes(image)
            resp = requests.post(
                _ENDPOINT, files={"file": ("image.png", data)}, data=payload, timeout=60
            )
        result = resp.json()

        if result.get("IsErroredOnProcessing"):
            msg = result.get("ErrorMessage") or result.get("ErrorDetails") or result
            raise RuntimeError(f"OCR.space error: {msg}")

        parsed = (result.get("ParsedResults") or [{}])[0]
        text = parsed.get("ParsedText", "") or ""

        blocks = []
        for line in (parsed.get("TextOverlay") or {}).get("Lines", []):
            for word in line.get("Words", []):
                x = word.get("Left", 0)
                y = word.get("Top", 0)
                w = word.get("Width", 0)
                h = word.get("Height", 0)
                blocks.append(
                    make_block(
                        word.get("WordText", ""),
                        bbox=(x, y, x + w, y + h),
                        level="word",
                    )
                )

        return OcrResult.from_blocks(
            blocks, backend=self.backend_id, raw=result, text=text
        )
