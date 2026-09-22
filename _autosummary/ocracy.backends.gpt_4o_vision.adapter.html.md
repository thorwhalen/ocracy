# ocracy.backends.gpt_4o_vision.adapter

Adapter for OpenAI GPT-4o vision — image -> transcribed text via the openai SDK.

VLM OCR is text-oriented (no per-word boxes/confidence): the model’s transcription
becomes `result.text`. Pass a custom `prompt` for structured extraction. Uses
the official `openai` SDK’s chat-completions image-input format.

### Classes

| [`Adapter`](#ocracy.backends.gpt_4o_vision.adapter.Adapter)(config)   | OpenAI GPT-4o vision adapter.   |
|--------------------------------------------------------------------|---------------------------------|

### *class* ocracy.backends.gpt_4o_vision.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

OpenAI GPT-4o vision adapter.
