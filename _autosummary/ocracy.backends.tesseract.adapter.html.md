# ocracy.backends.tesseract.adapter

Adapter for Tesseract — image -> text+word-boxes via pytesseract.

A worked example of the adapter contract:

1. Normalize the input to a PIL image (`ocracy.util.to_pil`).
2. Call the engine *inside* `_read` (lazy import of `pytesseract`).
3. Map Tesseract’s TSV-style word rows into normalized `TextBlock``s (boxes +
   confidence rescaled 0..100 -> 0..1) and assemble reading-order text, keeping
   the raw dict in ``raw=`.

### Classes

| [`Adapter`](#ocracy.backends.tesseract.adapter.Adapter)(config)   | Tesseract adapter.   |
|--------------------------------------------------------------------|----------------------|

### *class* ocracy.backends.tesseract.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

Tesseract adapter.
