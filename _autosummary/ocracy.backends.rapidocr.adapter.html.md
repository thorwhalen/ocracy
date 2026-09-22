# ocracy.backends.rapidocr.adapter

Adapter for RapidOCR — image -> text + quad boxes via ONNXRuntime PP-OCR.

### Classes

| [`Adapter`](#ocracy.backends.rapidocr.adapter.Adapter)(config)   | RapidOCR adapter (lazily builds and caches one engine).   |
|--------------------------------------------------------------------|-----------------------------------------------------------|

### *class* ocracy.backends.rapidocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

RapidOCR adapter (lazily builds and caches one engine).
