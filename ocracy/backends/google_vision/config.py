"""Configuration for the Google Cloud Vision backend.

``languages`` (ISO-639-1) maps to Vision ``language_hints``. ``document=True``
(default) uses DOCUMENT_TEXT_DETECTION (dense text + handwriting + structure);
``document=False`` uses TEXT_DETECTION (sparse/scene text). Auth is Google ADC —
set ``GOOGLE_APPLICATION_CREDENTIALS`` to a service-account JSON
(https://cloud.google.com/vision/docs/setup).
"""

BACKEND_CONFIG = {
    "id": "google-vision",
    "name": "google-vision",
    "display_name": "Google Cloud Vision OCR",
    "pip_install": "google-cloud-vision",
    "import_name": "google.cloud.vision",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["handwriting", "layout"],
    "default_for": [],
    "api_env_var": "GOOGLE_APPLICATION_CREDENTIALS",
    "description": (
        "High-accuracy cloud OCR across many languages and scripts, including "
        "handwriting, with block/paragraph/word structure and bounding boxes."
    ),
    "param_map": {
        "languages": {"native_name": "language_hints"},
        "document": {"native_name": "document", "default": True},
    },
}
