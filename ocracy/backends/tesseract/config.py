"""Configuration for the Tesseract backend.

Demonstrates the ``param_map`` pattern: ocracy's normalized ``languages`` (a list
of ISO-639-1 codes like ``["en", "fr"]``) is coerced to Tesseract's native
``lang`` string (``"eng+fra"``). ``psm`` / ``oem`` / ``config`` are passed through
and assembled into a Tesseract config string by the adapter.
"""

# ISO-639-1 (and a few common aliases) -> Tesseract 3-letter language codes.
_ISO1_TO_TESS = {
    "en": "eng", "fr": "fra", "de": "deu", "es": "spa", "it": "ita",
    "pt": "por", "nl": "nld", "ru": "rus", "uk": "ukr", "pl": "pol",
    "zh": "chi_sim", "zh-cn": "chi_sim", "zh-tw": "chi_tra", "ja": "jpn",
    "ko": "kor", "ar": "ara", "he": "heb", "hi": "hin", "el": "ell",
    "tr": "tur", "sv": "swe", "no": "nor", "da": "dan", "fi": "fin",
    "cs": "ces", "ro": "ron", "hu": "hun", "vi": "vie", "th": "tha",
}


def _to_tess_lang(languages):
    """Coerce ``languages`` (str or list of codes) into a Tesseract ``lang`` string."""
    if languages is None:
        return None
    if isinstance(languages, str):
        # Already a Tesseract spec ("eng+fra") or a single code.
        if "+" in languages or len(languages) == 3:
            return languages
        return _ISO1_TO_TESS.get(languages.lower(), languages)
    # Iterable of codes.
    codes = [
        c if (len(c) == 3 or "+" in c) else _ISO1_TO_TESS.get(c.lower(), c)
        for c in languages
    ]
    return "+".join(codes)


BACKEND_CONFIG = {
    "id": "tesseract",
    "name": "tesseract",
    "display_name": "Tesseract (pytesseract)",
    "pip_install": "pytesseract Pillow",
    "import_name": "pytesseract",
    "license": "Apache-2.0",
    "is_local": True,
    "is_remote": False,
    "capabilities": [],
    "default_for": ["read"],
    "api_env_var": "",
    "description": (
        "Local, free, offline OCR for printed text in 100+ languages, with word "
        "boxes and confidences. Requires the system 'tesseract' binary."
    ),
    "param_map": {
        "languages": {"native_name": "lang", "coerce": _to_tess_lang},
        "lang": {"native_name": "lang"},
        "psm": {"native_name": "psm"},
        "oem": {"native_name": "oem"},
        "config": {"native_name": "config"},
    },
}
