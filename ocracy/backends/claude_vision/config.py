"""Configuration for the Claude (Anthropic) vision backend.

A vision-language-model OCR: send the image to Claude and ask it to transcribe.
Excels at messy, handwritten, and structured content (it can also follow a custom
``prompt`` to extract fields), but returns plain text/Markdown with no bounding
boxes or confidences. Needs ``ANTHROPIC_API_KEY``.

``model`` defaults to ``claude-opus-4-8`` (most capable); override with a cheaper
vision model such as ``claude-haiku-4-5`` for high-volume, cost-sensitive OCR.
"""

BACKEND_CONFIG = {
    "id": "claude-vision",
    "name": "claude-vision",
    "display_name": "Claude (Anthropic) Vision",
    "pip_install": "anthropic",
    "import_name": "anthropic",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["handwriting", "math", "tables", "layout", "key_value"],
    "default_for": [],
    "api_env_var": "ANTHROPIC_API_KEY",
    "description": (
        "VLM 'read + reason' OCR via Claude vision — strong on messy/handwritten/"
        "structured docs and prompt-driven field extraction; no boxes/confidence."
    ),
    "param_map": {
        "model": {"native_name": "model", "default": "claude-opus-4-8"},
        "prompt": {"native_name": "prompt"},
        "max_tokens": {"native_name": "max_tokens", "default": 16000},
    },
}
