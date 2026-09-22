# ocracy.backends.trocr_handwritten.adapter

Adapter for TrOCR (handwritten) — image of a text line -> text, locally.

Loads a HuggingFace `VisionEncoderDecoderModel` + `TrOCRProcessor` (cached per
checkpoint) and decodes one line of (hand)written text. TrOCR is line-level: the
recognized line is `result.text`.

### Classes

| [`Adapter`](#ocracy.backends.trocr_handwritten.adapter.Adapter)(config)   | TrOCR adapter (caches the processor + model per checkpoint).   |
|--------------------------------------------------------------------|----------------------------------------------------------------|

### *class* ocracy.backends.trocr_handwritten.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

TrOCR adapter (caches the processor + model per checkpoint).
