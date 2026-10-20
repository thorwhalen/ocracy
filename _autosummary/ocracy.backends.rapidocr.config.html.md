# ocracy.backends.rapidocr.config

Configuration for the RapidOCR backend (ONNXRuntime).

`rapidocr` 3.x runs the PP-OCRv6 models via ONNXRuntime — PaddleOCR-grade
accuracy (the same models) with a light, framework-free install. PP-OCRv6 is
multilingual: `languages` (ISO-639-1; the first is used) selects the
recogniser’s script set, and `model_size` (`tiny` / `small` / `medium`,
default `medium`) trades speed for accuracy: medium is about 2.5 s a page on a
CPU, near-perfect on clean and degraded print; the older PP-OCRv4 mobile models
read about 0.5 s a page but made about 10% character errors on clean print
([https://github.com/thorwhalen/ocracy/issues/22](https://github.com/thorwhalen/ocracy/issues/22)). An unsupported language is
refused by the engine, listing the ones it supports.

An existing install with only `rapidocr_onnxruntime` still works (see the
adapter), which is why that package is an `import_alternatives` entry.
