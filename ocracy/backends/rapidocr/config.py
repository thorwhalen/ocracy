"""Configuration for the RapidOCR backend (ONNXRuntime).

RapidOCR runs the PP-OCR models via ONNXRuntime — PaddleOCR-grade accuracy with a
light, framework-free install and fast CPU inference. It bundles multilingual
models and selects scripts internally, so there is no per-call ``languages``
parameter; callers can still tune detection/recognition via ``**kwargs``.
"""

BACKEND_CONFIG = {
    "id": "rapidocr",
    "name": "rapidocr",
    "display_name": "RapidOCR",
    "pip_install": "rapidocr-onnxruntime",
    "import_name": "rapidocr_onnxruntime",
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
    # RapidOCR takes its tuning via the engine call, not a fixed schema; ocracy
    # passes unknown kwargs straight through (no param_map entries to translate).
    "param_map": {},
}
