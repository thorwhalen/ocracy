"""Configuration for the PaddleOCR backend.

PaddleOCR's PP-OCR models are among the most accurate open engines, especially for
CJK, across 100+ languages. ``languages`` (ISO-639-1) becomes PaddleOCR's
``lang``: ISO codes on 3.x (``zh`` -> ``ch``, ``ja`` -> ``japan``), the 2.x names on
2.x (``fr`` -> ``french``, ``ru`` -> ``cyrillic``). The adapter caches one
engine per language. (Table/layout extraction is PP-StructureV3 — a separate ledger
entry, ``paddleocr-ppstructure``; this façade wraps the text OCR.)
"""

# ISO-639-1 -> PaddleOCR ``lang`` codes. 3.x takes ISO codes for most languages
# and refuses 2.x's script names (``cyrillic``, ``devanagari``, ``arabic``); 2.x
# needs them. A code missing from the map is passed through as given.
V3_LANG = {
    "zh": "ch",
    "zh-cn": "ch",
    "zh-tw": "chinese_cht",
    "ja": "japan",
    "ko": "korean",
}
V2_LANG = {
    **V3_LANG,
    "fr": "french",
    "de": "german",
    "ru": "cyrillic",
    "ar": "arabic",
    "hi": "devanagari",
}


def first_language(languages):
    """ocracy's ``languages`` -> the one code PaddleOCR takes (lower-cased), ``en`` if unset.

    The adapter maps it to the installed PaddleOCR's spelling (:data:`V3_LANG` /
    :data:`V2_LANG`); ``paddleocr-ppstructure`` uses the same coercion.
    """
    if languages is None:
        return "en"
    code = languages[0] if isinstance(languages, (list, tuple)) else languages
    return str(code).lower()


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
        "languages": {
            "native_name": "lang",
            "coerce": first_language,
            "default": "en",
        },
    },
}
