# ocracy.backends.paddleocr.config

Configuration for the PaddleOCR backend.

PaddleOCR’s PP-OCR models are among the most accurate open engines, especially for
CJK, across 100+ languages. `languages` (ISO-639-1) is coerced to PaddleOCR’s own
`lang` codes (`fr` -> `french`, `zh` -> `ch`, …). The adapter caches one
engine per language. (Table/layout extraction is PP-StructureV3 — a separate ledger
entry, `paddleocr-ppstructure`; this façade wraps the text OCR.)
