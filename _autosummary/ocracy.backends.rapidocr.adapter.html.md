# ocracy.backends.rapidocr.adapter

Adapter for RapidOCR — image -> text + quad boxes via ONNXRuntime PP-OCR.

`rapidocr` 3.x runs the same PP-OCRv6 models as PaddleOCR through ONNX, without
PaddlePaddle (measured in [https://github.com/thorwhalen/ocracy/issues/22](https://github.com/thorwhalen/ocracy/issues/22)). Its
result is an object with `boxes` / `txts` / `scores` (all `None` when
nothing is found). The adapter builds the v6 pipeline at the requested `lang` and
`model_size` (one engine cached per pair).

An install that only has the older `rapidocr_onnxruntime` package (PP-OCRv4,
which can drop word spaces) keeps working: the adapter falls back to it, ignores
`lang` / `model_size` there (that package selects scripts itself).

### Module Attributes

| [`OCR_VERSION`](#ocracy.backends.rapidocr.adapter.OCR_VERSION)   | PP-OCRv6 is multilingual, so `lang` selects the recogniser's script set and `model_size` the size of both detector and recogniser.   |
|----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|

### Functions

| [`blocks_from_legacy`](#ocracy.backends.rapidocr.adapter.blocks_from_legacy)(result)   | Line blocks from `rapidocr_onnxruntime`'s `[[box, text, score], ...]` (or `None`).   |
|-------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`blocks_from_v3`](#ocracy.backends.rapidocr.adapter.blocks_from_v3)(result)       | Line blocks from a 3.x result object (`boxes` / `txts` / `scores`).                  |
| [`is_v3_package`](#ocracy.backends.rapidocr.adapter.is_v3_package)()              | Whether the `rapidocr` 3.x package (not just the legacy one) is importable.          |
| [`v6_params`](#ocracy.backends.rapidocr.adapter.v6_params)(lang, model_size)  | The `RapidOCR(params=...)` dict that selects PP-OCRv6 at `lang` and `model_size`.    |

### Classes

| [`Adapter`](#ocracy.backends.rapidocr.adapter.Adapter)(config)   | RapidOCR adapter (caches one engine per `(lang, model_size)`).   |
|--------------------------------------------------------------------|------------------------------------------------------------------|

### *class* ocracy.backends.rapidocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

RapidOCR adapter (caches one engine per `(lang, model_size)`).

### ocracy.backends.rapidocr.adapter.OCR_VERSION *= 'PP-OCRv6'*

PP-OCRv6 is multilingual, so `lang` selects the recogniser’s script set and
`model_size` the size of both detector and recogniser.

### ocracy.backends.rapidocr.adapter.blocks_from_legacy(result)

Line blocks from `rapidocr_onnxruntime`’s `[[box, text, score], ...]` (or `None`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.backends.rapidocr.adapter.blocks_from_v3(result)

Line blocks from a 3.x result object (`boxes` / `txts` / `scores`).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.backends.rapidocr.adapter.is_v3_package()

Whether the `rapidocr` 3.x package (not just the legacy one) is importable.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.backends.rapidocr.adapter.v6_params(lang, model_size)

The `RapidOCR(params=...)` dict that selects PP-OCRv6 at `lang` and `model_size`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
