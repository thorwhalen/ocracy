"""Configuration for the ocrmac backend (Apple Vision, macOS-only).

Wraps the on-device macOS Vision OCR. ``languages`` (ISO-639-1) is coerced to
Vision's BCP-47 preference codes (``en`` -> ``en-US``). ``recognition_level``
trades speed for accuracy (``"fast"`` / ``"accurate"``). Handwriting works
automatically. macOS only.
"""

# ISO-639-1 -> Apple Vision language preference (BCP-47-ish) codes.
_ISO1_TO_VISION = {
    "en": "en-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "it": "it-IT",
    "pt": "pt-BR",
    "nl": "nl-NL",
    "zh": "zh-Hans",
    "zh-cn": "zh-Hans",
    "zh-tw": "zh-Hant",
    "ja": "ja-JP",
    "ko": "ko-KR",
    "ru": "ru-RU",
    "uk": "uk-UA",
    "ar": "ar-SA",
    "th": "th-TH",
    "vi": "vi-VT",
}


def _to_vision_langs(languages):
    if languages is None:
        return None
    if isinstance(languages, str):
        languages = [languages]
    return [
        c if "-" in str(c) else _ISO1_TO_VISION.get(str(c).lower(), c)
        for c in languages
    ]


BACKEND_CONFIG = {
    "id": "ocrmac",
    "name": "ocrmac",
    "display_name": "ocrmac (Apple Vision)",
    "pip_install": "ocrmac",
    "import_name": "ocrmac",
    "license": "MIT",
    "is_local": True,
    "is_remote": False,
    "capabilities": ["handwriting"],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "Fast, free, fully on-device OCR via the macOS Vision framework, including "
        "handwriting; returns line text with confidence and bounding boxes. "
        "macOS only."
    ),
    "param_map": {
        "languages": {
            "native_name": "language_preference",
            "coerce": _to_vision_langs,
        },
        "recognition_level": {
            "native_name": "recognition_level",
            "default": "accurate",
        },
    },
}
