"""Configuration for the OpenAI GPT-4o vision backend.

A vision-language-model OCR via OpenAI's chat completions with image input.
Like other VLM OCR: great at messy/handwritten/structured content and
prompt-driven extraction, but no bounding boxes or confidences. Needs
``OPENAI_API_KEY``. ``model`` defaults to ``gpt-4o`` (override e.g. ``gpt-4o-mini``).
"""

BACKEND_CONFIG = {
    "id": "gpt-4o-vision",
    "name": "gpt-4o-vision",
    "display_name": "OpenAI GPT-4o Vision",
    "pip_install": "openai",
    "import_name": "openai",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["handwriting", "math", "tables", "key_value", "charts"],
    "default_for": [],
    "api_env_var": "OPENAI_API_KEY",
    "description": (
        "VLM 'read + reason' OCR via OpenAI GPT-4o vision — strong on messy/"
        "handwritten/structured docs and prompt-driven extraction; no boxes/confidence."
    ),
    "param_map": {
        "model": {"native_name": "model", "default": "gpt-4o"},
        "prompt": {"native_name": "prompt"},
        "max_tokens": {"native_name": "max_tokens", "default": 4096},
    },
}
