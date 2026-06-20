"""Adapter for OpenAI GPT-4o vision — image -> transcribed text via the openai SDK.

VLM OCR is text-oriented (no per-word boxes/confidence): the model's transcription
becomes ``result.text``. Pass a custom ``prompt`` for structured extraction. Uses
the official ``openai`` SDK's chat-completions image-input format.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter


class Adapter(BaseOcrAdapter):
    """OpenAI GPT-4o vision adapter."""

    DEFAULT_PROMPT = (
        "Transcribe ALL text in this image exactly as it appears, preserving "
        "reading order and layout. Output only the transcribed text — no commentary."
    )

    def _read(
        self, image, *, model="gpt-4o", prompt=None, max_tokens=4096, **extra
    ) -> OcrResult:
        from ocracy.credentials import resolve_credential

        api_key = resolve_credential(
            "openai",
            api_key=extra.pop("api_key", None),
            env_var=self.config.get("api_env_var"),
        )

        import base64

        from openai import OpenAI

        from ocracy.util import load_image_bytes

        data = load_image_bytes(image, fmt="PNG")
        b64 = base64.b64encode(data).decode("ascii")

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or self.DEFAULT_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{b64}"},
                        },
                    ],
                }
            ],
        )

        text = response.choices[0].message.content or ""
        return OcrResult.from_text(
            text, backend=self.backend_id, raw=response, model=model, markdown=text
        )
