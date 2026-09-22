# ocracy.backends.gpt_4o_vision.config

Configuration for the OpenAI GPT-4o vision backend.

A vision-language-model OCR via OpenAI’s chat completions with image input.
Like other VLM OCR: great at messy/handwritten/structured content and
prompt-driven extraction, but no bounding boxes or confidences. Needs
`OPENAI_API_KEY`. `model` defaults to `gpt-4o` (override e.g. `gpt-4o-mini`).
