"""Configuration for the TrOCR (handwritten) backend.

Local, offline handwriting recognition via HuggingFace TrOCR transformer models.
NOTE: TrOCR recognizes a single text line per image — for full pages, segment into
line crops upstream and call once per line. Heavy (PyTorch + transformers); first
run downloads the model. ``model_name`` selects the checkpoint.
"""

BACKEND_CONFIG = {
    "id": "trocr-handwritten",
    "name": "trocr-handwritten",
    "display_name": "TrOCR (handwritten)",
    "pip_install": "transformers torch Pillow",
    "import_name": "transformers",
    "license": "MIT",
    "is_local": True,
    "is_remote": False,
    "capabilities": ["handwriting"],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "Local, offline handwriting OCR (HuggingFace TrOCR). Single line per image — "
        "segment pages into lines upstream."
    ),
    "param_map": {
        "model_name": {
            "native_name": "model_name",
            "default": "microsoft/trocr-base-handwritten",
        },
    },
}
