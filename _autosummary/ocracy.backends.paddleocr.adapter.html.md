# ocracy.backends.paddleocr.adapter

Adapter for PaddleOCR — image -> text + quad boxes via PP-OCR.

PaddleOCR 3.x replaced the 2.x API: the constructor refuses 2.x keywords such as
`show_log`, `predict()` returns result objects holding `rec_texts` /
`rec_scores` / `rec_polys` instead of 2.x `ocr()`’s `[[box, (text, score)],
...]`, and language names changed (3.x takes ISO codes). The adapter tells the two
apart by whether `PaddleOCR` has `predict` (2.x accepts any keyword, so a
constructor error cannot), then builds and parses accordingly. The 3.x document
pre-processors (page orientation, unwarping, text-line orientation) are off: they
are for photographed pages, and they slow every call. Engines are cached per
language.

### Functions

| [`blocks_from_v2`](#ocracy.backends.paddleocr.adapter.blocks_from_v2)(page)   | Line blocks from one 2.x page (`[[box, (text, score)], ...]`).              |
|-------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`blocks_from_v3`](#ocracy.backends.paddleocr.adapter.blocks_from_v3)(page)   | Line blocks from one 3.x result (`rec_texts` / `rec_scores` / `rec_polys`). |
| [`is_v3`](#ocracy.backends.paddleocr.adapter.is_v3)(paddle_class)    | Whether a PaddleOCR pipeline class has the 3.x API (`predict`).             |

### Classes

| [`Adapter`](#ocracy.backends.paddleocr.adapter.Adapter)(config)   | PaddleOCR adapter (caches one engine per language).   |
|--------------------------------------------------------------------|-------------------------------------------------------|

### *class* ocracy.backends.paddleocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

PaddleOCR adapter (caches one engine per language).

### ocracy.backends.paddleocr.adapter.blocks_from_v2(page)

Line blocks from one 2.x page (`[[box, (text, score)], ...]`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.backends.paddleocr.adapter.blocks_from_v3(page)

Line blocks from one 3.x result (`rec_texts` / `rec_scores` / `rec_polys`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.backends.paddleocr.adapter.is_v3(paddle_class)

Whether a PaddleOCR pipeline class has the 3.x API (`predict`).

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
