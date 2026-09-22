# ocracy.backends.ocr_space.config

Configuration for the OCR.space backend (REST API).

A zero-install cloud OCR with a generous free tier. `languages` (ISO-639-1) is
coerced to OCR.space’s 3-letter codes (`en` -> `eng`). `ocr_engine` selects
engine 1/2/3 (2 is the multilingual default). Needs an `OCR_SPACE_API_KEY`
(free key at [https://ocr.space/ocrapi/freekey](https://ocr.space/ocrapi/freekey)).
