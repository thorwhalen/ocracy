# ocracy.backends.paddleocr_ppstructure.adapter

Adapter for PaddleOCR PP-StructureV3 — image -> Markdown with tables, plus text lines.

`result.markdown` is the document as PP-StructureV3 renders it: headings and
paragraphs as Markdown, tables as HTML, formulas as LaTeX. `result.blocks` are
the PP-OCR text lines it found along the way (`level="line"`), so `result.lines`
works as with `paddleocr`; `result.text` joins those lines.

PP-StructureV3 needs PaddleOCR’s `doc-parser` extra on top of `paddleocr`. When
it is missing, PaddleOCR raises a `RuntimeError` at construction; the adapter
turns that into an `ImportError` that names the install line.

### Classes

| [`Adapter`](#ocracy.backends.paddleocr_ppstructure.adapter.Adapter)(config)   | PP-StructureV3 adapter (caches one pipeline per language).   |
|--------------------------------------------------------------------|--------------------------------------------------------------|

### *class* ocracy.backends.paddleocr_ppstructure.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

PP-StructureV3 adapter (caches one pipeline per language).
