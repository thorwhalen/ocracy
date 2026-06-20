"""Adapter for Claude vision — image -> transcribed text via the Anthropic SDK.

VLM OCR is text-oriented (no per-word boxes/confidence): the model's transcription
becomes ``result.text``. Pass a custom ``prompt`` to do structured extraction
instead of plain transcription. Uses the official ``anthropic`` SDK and the
base64 image content-block format.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter


class Adapter(BaseOcrAdapter):
    """Anthropic Claude vision adapter."""

    DEFAULT_PROMPT = (
        "Transcribe ALL text in this image exactly as it appears, preserving "
        "reading order and layout. Output only the transcribed text — no commentary, "
        "no preface, no explanation."
    )

    def _read(
        self, image, *, model="claude-opus-4-8", prompt=None, max_tokens=16000, **extra
    ) -> OcrResult:
        from ocracy.credentials import resolve_credential

        api_key = resolve_credential(
            "anthropic",
            api_key=extra.pop("api_key", None),
            env_var=self.config.get("api_env_var"),
        )

        import base64

        import anthropic

        from ocracy.util import load_image_bytes

        data = load_image_bytes(image, fmt="PNG")
        b64 = base64.standard_b64encode(data).decode("utf-8")

        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": prompt or self.DEFAULT_PROMPT},
                    ],
                }
            ],
        )

        text = "".join(
            b.text for b in message.content if getattr(b, "type", None) == "text"
        )
        return OcrResult.from_text(
            text, backend=self.backend_id, raw=message, model=model, markdown=text
        )
