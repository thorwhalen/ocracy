# ocracy.backends.mistral_ocr.adapter

Adapter for Mistral OCR — image -> Markdown via the Mistral OCR API.

Mistral OCR is text/markdown-oriented (no per-word boxes or confidence): the
payload is per-page Markdown, joined into `result.text` and `result.markdown`,
with the raw SDK response in `result.raw`.

### Classes

| [`Adapter`](#ocracy.backends.mistral_ocr.adapter.Adapter)(config)   | Mistral OCR API adapter.   |
|--------------------------------------------------------------------|----------------------------|

### *class* ocracy.backends.mistral_ocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.md#ocracy.make_backend.BaseOcrAdapter)

Mistral OCR API adapter.
