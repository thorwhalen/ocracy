# ocracy.backends.paddleocr_ppstructure.config

Configuration for the PaddleOCR PP-StructureV3 backend.

PP-StructureV3 is PaddleOCR’s document parser: layout detection, table structure
recognition and formula recognition on top of the PP-OCR text models, rendered as
Markdown (tables as HTML inside it). It is the capability RapidOCR and the plain
`paddleocr` backend do not have, and it is slow on CPU: about 25 s a page on an
Apple-silicon Mac, after a first-run download of the models (about 3 minutes).
See [https://github.com/thorwhalen/ocracy/issues/1](https://github.com/thorwhalen/ocracy/issues/1) for the measurements.

`languages` is handled exactly as for `paddleocr` (the same text models).
