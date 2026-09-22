# ocracy.backends.paddleocr.adapter

Adapter for PaddleOCR — image -> text + quad boxes via PP-OCR.

PaddleOCR’s constructor and `ocr()` signatures have shifted across major versions
(`use_angle_cls`/`cls` in 2.x vs `use_textline_orientation` in 3.x), so this
adapter probes a couple of signatures defensively and parses the classic
`[[ [box, (text, score)], ... ]]` result. Engines are cached per language.

### Classes

| [`Adapter`](#ocracy.backends.paddleocr.adapter.Adapter)(config)   | PaddleOCR adapter (caches one engine per language).   |
|--------------------------------------------------------------------|-------------------------------------------------------|

### *class* ocracy.backends.paddleocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

PaddleOCR adapter (caches one engine per language).
