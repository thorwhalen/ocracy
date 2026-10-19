# ocracy.backends.paddleocr.config

Configuration for the PaddleOCR backend.

PaddleOCR’s PP-OCR models are among the most accurate open engines, especially for
CJK, across 100+ languages. `languages` (ISO-639-1) becomes PaddleOCR’s
`lang`: ISO codes on 3.x (`zh` -> `ch`, `ja` -> `japan`), the 2.x names on
2.x (`fr` -> `french`, `ru` -> `cyrillic`). The adapter caches one
engine per language. (Table/layout extraction is PP-StructureV3 — a separate ledger
entry, `paddleocr-ppstructure`; this façade wraps the text OCR.)

### Functions

| [`first_language`](#ocracy.backends.paddleocr.config.first_language)(languages)   | ocracy's `languages` -> the one code PaddleOCR takes (lower-cased), `en` if unset.   |
|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|

### ocracy.backends.paddleocr.config.first_language(languages)

ocracy’s `languages` -> the one code PaddleOCR takes (lower-cased), `en` if unset.

The adapter maps it to the installed PaddleOCR’s spelling (`V3_LANG` /
`V2_LANG`); `paddleocr-ppstructure` uses the same coercion.
