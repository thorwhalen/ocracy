# ocracy.backends.easyocr.config

Configuration for the EasyOCR backend.

`languages` (a list of ISO-639-1 codes) is coerced to EasyOCR’s `lang_list`
(mostly the same codes; Chinese maps to `ch_sim` / `ch_tra`). `gpu` toggles
CUDA use. EasyOCR readers are expensive to build, so the adapter caches one per
(language-set, gpu) combination.
