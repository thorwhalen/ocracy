"""Configuration for the EasyOCR backend.

``languages`` (a list of ISO-639-1 codes) is coerced to EasyOCR's ``lang_list``
(mostly the same codes; Chinese maps to ``ch_sim`` / ``ch_tra``). ``gpu`` toggles
CUDA use. EasyOCR readers are expensive to build, so the adapter caches one per
(language-set, gpu) combination.
"""

# EasyOCR mostly uses ISO-639-1 codes; the notable exceptions are Chinese.
_ISO1_TO_EASY = {"zh": "ch_sim", "zh-cn": "ch_sim", "zh-tw": "ch_tra"}


def _to_easy_langs(languages):
    if languages is None:
        return ["en"]
    if isinstance(languages, str):
        languages = [languages]
    return [_ISO1_TO_EASY.get(str(c).lower(), c) for c in languages]


BACKEND_CONFIG = {
    "id": "easyocr",
    "name": "easyocr",
    "display_name": "EasyOCR",
    "pip_install": "easyocr",
    "import_name": "easyocr",
    "license": "Apache-2.0",
    "is_local": True,
    "is_remote": False,
    "capabilities": [],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "Local, offline, multilingual OCR (80+ languages) returning polygon boxes "
        "and confidence; strong on scene/photo text. Pure pip install."
    ),
    "param_map": {
        "languages": {
            "native_name": "lang_list",
            "coerce": _to_easy_langs,
            "default": ["en"],
        },
        "gpu": {"native_name": "gpu", "default": False},
    },
}
