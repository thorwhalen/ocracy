"""Configuration for the Mistral OCR backend (cloud VLM document OCR).

A modern, cheap (~$1–2 / 1,000 pages) VLM OCR that returns clean Markdown with
structure, math, and tables. Text-oriented (no per-word boxes/confidence). Needs a
``MISTRAL_API_KEY`` (https://console.mistral.ai/api-keys).
"""

BACKEND_CONFIG = {
    "id": "mistral-ocr",
    "name": "mistral-ocr",
    "display_name": "Mistral OCR",
    "pip_install": "mistralai",
    "import_name": "mistralai",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["math", "tables", "layout"],
    "default_for": [],
    "api_env_var": "MISTRAL_API_KEY",
    "description": (
        "Cheap, modern VLM document OCR returning clean Markdown with structure, "
        "math, and tables. Multilingual; cloud-only."
    ),
    "param_map": {
        "model": {"native_name": "model", "default": "mistral-ocr-latest"},
    },
}
