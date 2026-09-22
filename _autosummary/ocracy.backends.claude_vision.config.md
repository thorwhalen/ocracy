# ocracy.backends.claude_vision.config

Configuration for the Claude (Anthropic) vision backend.

A vision-language-model OCR: send the image to Claude and ask it to transcribe.
Excels at messy, handwritten, and structured content (it can also follow a custom
`prompt` to extract fields), but returns plain text/Markdown with no bounding
boxes or confidences. Needs `ANTHROPIC_API_KEY`.

`model` defaults to `claude-opus-4-8` (most capable); override with a cheaper
vision model such as `claude-haiku-4-5` for high-volume, cost-sensitive OCR.
