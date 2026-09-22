# ocracy.backends.rapidocr.config

Configuration for the RapidOCR backend (ONNXRuntime).

RapidOCR runs the PP-OCR models via ONNXRuntime — PaddleOCR-grade accuracy with a
light, framework-free install and fast CPU inference. It bundles multilingual
models and selects scripts internally, so there is no per-call `languages`
parameter; callers can still tune detection/recognition via `**kwargs`.
