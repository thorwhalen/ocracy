"""Configuration for the PaddleOCR backend.

PaddleOCR's PP-OCR models are among the most accurate open engines, especially for
CJK, across 100+ languages. ``languages`` (ISO-639-1) is coerced to PaddleOCR's own
``lang`` codes (``fr`` -> ``french``, ``zh`` -> ``ch``, ...). The adapter caches one
engine per language. (Table/layout extraction is PP-StructureV3 — a separate ledger
entry, ``paddleocr-ppstructure``; this façade wraps the text OCR.)
"""

# ISO-639-1 -> PaddleOCR language codes (PaddleOCR uses some full names).
_ISO1_TO_PADDLE = {
    "en": "en", "zh": "ch", "zh-cn": "ch", "zh-tw": "chinese_cht",
    "fr": "french", "de": "german", "ja": "japan", "ko": "korean",
    "ru": "cyrillic", "ar": "arabic", "hi": "devanagari", "ta": "ta",
    "te": "te", "it": "it", "es": "es", "pt": "pt", "nl": "nl",
}


def _to_paddle_lang(languages):
    if languages is None:
        return "en"
    code = languages[0] if isinstance(languages, (list, tuple)) else languages
    return _ISO1_TO_PADDLE.get(str(code).lower(), str(code))


BACKEND_CONFIG = {
    "id": "paddleocr",
    "name": "paddleocr",
    "display_name": "PaddleOCR (PP-OCR)",
    "pip_install": "paddleocr paddlepaddle",
    "import_name": "paddleocr",
    "license": "Apache-2.0",
    "is_local": True,
    "is_remote": False,
    "capabilities": [],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "Among the most accurate open OCR engines (especially CJK), 100+ languages, "
        "with polygon boxes and confidence. CPU-capable; GPU helps."
    ),
    "param_map": {
        "languages": {"native_name": "lang", "coerce": _to_paddle_lang, "default": "en"},
    },
}
