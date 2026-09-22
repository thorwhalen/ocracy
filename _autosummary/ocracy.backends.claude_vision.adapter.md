# ocracy.backends.claude_vision.adapter

Adapter for Claude vision — image -> transcribed text via the Anthropic SDK.

VLM OCR is text-oriented (no per-word boxes/confidence): the model’s transcription
becomes `result.text`. Pass a custom `prompt` to do structured extraction
instead of plain transcription. Uses the official `anthropic` SDK and the
base64 image content-block format.

### Classes

| [`Adapter`](#ocracy.backends.claude_vision.adapter.Adapter)(config)   | Anthropic Claude vision adapter.   |
|--------------------------------------------------------------------|------------------------------------|

### *class* ocracy.backends.claude_vision.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.md#ocracy.make_backend.BaseOcrAdapter)

Anthropic Claude vision adapter.
