"""Configuration for the PaddleOCR PP-StructureV3 backend.

PP-StructureV3 is PaddleOCR's document parser: layout detection, table structure
recognition and formula recognition on top of the PP-OCR text models, rendered as
Markdown (tables as HTML inside it). It is the capability RapidOCR and the plain
``paddleocr`` backend do not have, and it is slow on CPU: about 25 s a page on an
Apple-silicon Mac, after a first-run download of the models (about 3 minutes).
See https://github.com/thorwhalen/ocracy/issues/1 for the measurements.

``languages`` is coerced exactly as for ``paddleocr`` (the same text models).
"""

from ocracy.backends.paddleocr.config import to_paddle_lang

BACKEND_CONFIG = {
    "id": "paddleocr-ppstructure",
    "name": "paddleocr-ppstructure",
    "display_name": "PaddleOCR PP-StructureV3 (tables, layout, formulas)",
    "pip_install": 'paddleocr[doc-parser] paddlepaddle',
    "import_name": "paddleocr",
    "license": "Apache-2.0",
    "is_local": True,
    "is_remote": False,
    "capabilities": ["tables", "layout", "math"],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "PaddleOCR's document parser: tables (as HTML inside Markdown), layout "
        "regions and formulas, plus PP-OCR text lines. Local, CPU-capable but slow "
        "(tens of seconds a page); GPU helps."
    ),
    "param_map": {
        "languages": {
            "native_name": "lang",
            "coerce": to_paddle_lang,
            "default": "en",
        },
    },
}
