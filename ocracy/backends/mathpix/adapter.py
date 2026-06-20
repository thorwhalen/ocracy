"""Adapter for Mathpix — image -> Mathpix-Markdown / LaTeX via the Convert API.

Mathpix is a text-oriented (not box-oriented) engine: the primary payload is a
Markdown/LaTeX string, surfaced as ``result.text`` and ``result.markdown``; the
LaTeX form and confidence are kept in ``result.meta`` and the raw JSON in
``result.raw``.
"""

import os

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter

_ENDPOINT = "https://api.mathpix.com/v3/text"


class Adapter(BaseOcrAdapter):
    """Mathpix Convert API adapter."""

    def _read(self, image, *, formats=None, **extra) -> OcrResult:
        # Resolve credentials first (cheap, dependency-free) so a missing key fails
        # fast with guidance before we import/network.
        from ocracy.credentials import (
            MissingCredentialError,
            credential_help,
            resolve_credential,
        )

        app_key = resolve_credential(
            "mathpix",
            api_key=extra.pop("app_key", None),
            env_var=self.config.get("api_env_var"),
        )
        app_id = extra.pop("app_id", None) or os.environ.get("MATHPIX_APP_ID")
        if not app_id:
            raise MissingCredentialError(
                "Mathpix also needs MATHPIX_APP_ID.\n" + credential_help("mathpix")
            )

        import json as _json

        import requests

        from ocracy.util import load_image_bytes

        formats = formats or ["text", "latex_styled"]
        options = {"formats": formats, "math_inline_delimiters": ["$", "$"]}
        data = load_image_bytes(image)

        resp = requests.post(
            _ENDPOINT,
            files={"file": ("image.png", data)},
            data={"options_json": _json.dumps(options)},
            headers={"app_id": app_id, "app_key": app_key},
            timeout=60,
        )
        result = resp.json()
        if result.get("error"):
            raise RuntimeError(f"Mathpix error: {result.get('error')}")

        text = result.get("text", "") or ""
        meta = {"markdown": text}
        if result.get("latex_styled"):
            meta["latex"] = result["latex_styled"]
        if result.get("confidence") is not None:
            meta["confidence"] = result["confidence"]

        return OcrResult.from_text(text, backend=self.backend_id, raw=result, **meta)
