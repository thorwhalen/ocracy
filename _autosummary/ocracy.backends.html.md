# ocracy.backends

Implemented OCR backends.

Each real backend is a subpackage with a `config.py` (`BACKEND_CONFIG`) and an
`adapter.py` (`Adapter` with a `read` method). The registry
([`ocracy.registry`](ocracy.registry.html.md#module-ocracy.registry)) discovers them automatically. Subpackages whose name
starts with `_` (e.g. `ocracy.backends._template`) are scaffolding
helpers, not real backends, and are skipped by discovery.

To add a backend, scaffold one from the template:

```default
from ocracy.make_backend import scaffold_backend
scaffold_backend("easyocr")   # creates ocracy/backends/easyocr/ from the template
```

### Modules

| [`aws_textract`](ocracy.backends.aws_textract.html.md#module-ocracy.backends.aws_textract)                               | AWS Textract backend for ocracy (cloud OCR + forms/tables).                            |
|---------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| [`azure_document_intelligence`](ocracy.backends.azure_document_intelligence.html.md#module-ocracy.backends.azure_document_intelligence) | Azure AI Document Intelligence backend for ocracy (cloud read/layout).                 |
| [`claude_vision`](ocracy.backends.claude_vision.html.md#module-ocracy.backends.claude_vision)                             | Claude (Anthropic) vision backend for ocracy — VLM 'read + reason' OCR.                |
| [`easyocr`](ocracy.backends.easyocr.html.md#module-ocracy.backends.easyocr)                                         | EasyOCR backend for ocracy.                                                            |
| [`google_vision`](ocracy.backends.google_vision.html.md#module-ocracy.backends.google_vision)                             | Google Cloud Vision API (TEXT_DETECTION & DOCUMENT_TEXT_DETECTION) backend for ocracy. |
| [`gpt_4o_vision`](ocracy.backends.gpt_4o_vision.html.md#module-ocracy.backends.gpt_4o_vision)                             | OpenAI GPT-4o vision backend for ocracy — VLM 'read + reason' OCR.                     |
| [`mathpix`](ocracy.backends.mathpix.html.md#module-ocracy.backends.mathpix)                                         | Mathpix (Snip + Convert API) backend for ocracy.                                       |
| [`mistral_ocr`](ocracy.backends.mistral_ocr.html.md#module-ocracy.backends.mistral_ocr)                                 | Mistral OCR backend for ocracy (VLM document OCR via the Mistral API).                 |
| [`ocr_space`](ocracy.backends.ocr_space.html.md#module-ocracy.backends.ocr_space)                                     | OCR.space OCR API backend for ocracy.                                                  |
| [`ocrmac`](ocracy.backends.ocrmac.html.md#module-ocracy.backends.ocrmac)                                           | ocrmac (Apple Vision) backend for ocracy.                                              |
| [`paddleocr`](ocracy.backends.paddleocr.html.md#module-ocracy.backends.paddleocr)                                     | PaddleOCR backend for ocracy (PP-OCR text recognition).                                |
| [`pix2tex_latex_ocr`](ocracy.backends.pix2tex_latex_ocr.html.md#module-ocracy.backends.pix2tex_latex_ocr)                     | pix2tex (LaTeX-OCR) backend for ocracy — local math image -> LaTeX.                    |
| [`rapidocr`](ocracy.backends.rapidocr.html.md#module-ocracy.backends.rapidocr)                                       | RapidOCR backend for ocracy.                                                           |
| [`tesseract`](ocracy.backends.tesseract.html.md#module-ocracy.backends.tesseract)                                     | Tesseract backend for ocracy (via pytesseract).                                        |
| [`trocr_handwritten`](ocracy.backends.trocr_handwritten.html.md#module-ocracy.backends.trocr_handwritten)                     | TrOCR (handwritten) backend for ocracy — local handwriting recognition.                |
