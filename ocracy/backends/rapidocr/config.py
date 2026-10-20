"""Configuration for the RapidOCR backend (ONNXRuntime).

``rapidocr`` 3.x runs the PP-OCRv6 models via ONNXRuntime — PaddleOCR-grade
accuracy (the same models) with a light, framework-free install. PP-OCRv6 is
multilingual: ``languages`` (ISO-639-1; the first is used) selects the
recogniser's script set, and ``model_size`` (``tiny`` / ``small`` / ``medium``,
default ``medium``) trades speed for accuracy: medium is about 2.5 s a page on a
CPU, near-perfect on clean and degraded print; the older PP-OCRv4 mobile models
read about 0.5 s a page but made about 10% character errors on clean print
(https://github.com/thorwhalen/ocracy/issues/22). An unsupported language is
refused by the engine, listing the ones it supports.

An existing install with only ``rapidocr_onnxruntime`` still works (see the
adapter), which is why that package is an ``import_alternatives`` entry.
"""

from ocracy.backends.paddleocr.config import first_language

MODEL_SIZES = ("tiny", "small", "medium")


BACKEND_CONFIG = {
    "id": "rapidocr",
    "name": "rapidocr",
    "display_name": "RapidOCR",
    "pip_install": "rapidocr onnxruntime",
    "import_name": "rapidocr",
    "import_alternatives": ["rapidocr_onnxruntime"],
    "license": "Apache-2.0",
    "is_local": True,
    "is_remote": False,
    "capabilities": [],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "Fast, fully offline PP-OCR (CJK + Latin + more) via ONNXRuntime — "
        "PaddleOCR accuracy without the PaddlePaddle dependency."
    ),
    "param_map": {
        "languages": {"native_name": "lang", "coerce": first_language, "default": "en"},
        "model_size": {"native_name": "model_size", "choices": MODEL_SIZES, "default": "medium"},
    },
}
