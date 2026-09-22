# ocracy.backends.easyocr.adapter

Adapter for EasyOCR — image -> text + polygon boxes via easyocr.Reader.

### Classes

| [`Adapter`](#ocracy.backends.easyocr.adapter.Adapter)(config)   | EasyOCR adapter (caches one Reader per language-set + gpu flag).   |
|--------------------------------------------------------------------|--------------------------------------------------------------------|

### *class* ocracy.backends.easyocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.md#ocracy.make_backend.BaseOcrAdapter)

EasyOCR adapter (caches one Reader per language-set + gpu flag).
