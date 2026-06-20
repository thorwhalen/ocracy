"""Configuration for the OCR.space backend (REST API).

A zero-install cloud OCR with a generous free tier. ``languages`` (ISO-639-1) is
coerced to OCR.space's 3-letter codes (``en`` -> ``eng``). ``ocr_engine`` selects
engine 1/2/3 (2 is the multilingual default). Needs an ``OCR_SPACE_API_KEY``
(free key at https://ocr.space/ocrapi/freekey).
"""

# ISO-639-1 -> OCR.space language codes.
_ISO1_TO_OCRSPACE = {
    "ar": "ara", "bg": "bul", "zh": "chs", "zh-cn": "chs", "zh-tw": "cht",
    "hr": "hrv", "cs": "cze", "da": "dan", "nl": "dut", "en": "eng",
    "fi": "fin", "fr": "fre", "de": "ger", "el": "gre", "hu": "hun",
    "ko": "kor", "it": "ita", "ja": "jpn", "pl": "pol", "pt": "por",
    "ru": "rus", "sl": "slv", "es": "spa", "sv": "swe", "tr": "tur",
}


def _to_ocrspace_lang(languages):
    if languages is None:
        return "eng"
    code = languages[0] if isinstance(languages, (list, tuple)) else languages
    return _ISO1_TO_OCRSPACE.get(str(code).lower(), str(code))


BACKEND_CONFIG = {
    "id": "ocr-space",
    "name": "ocr-space",
    "display_name": "OCR.space OCR API",
    "pip_install": "requests",
    "import_name": "requests",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": [],
    "default_for": [],
    "api_env_var": "OCR_SPACE_API_KEY",
    "description": (
        "Zero-install cloud OCR with a generous free tier; good for plain printed "
        "text and quick prototypes. REST-only."
    ),
    "param_map": {
        "languages": {"native_name": "language", "coerce": _to_ocrspace_lang},
        "ocr_engine": {"native_name": "OCREngine", "default": 2},
        "overlay": {"native_name": "isOverlayRequired", "default": True},
        "detect_orientation": {"native_name": "detectOrientation"},
        "scale": {"native_name": "scale"},
        "table": {"native_name": "isTable"},
    },
}
