---
name: ocracy
description: >-
  Extract text from images, scans, screenshots, photos, or PDFs using the
  `ocracy` package — one uniform interface over many OCR engines (Tesseract,
  EasyOCR, PaddleOCR, Apple Vision, Google Vision, AWS Textract, Azure, Mathpix,
  Claude/GPT vision, ...). Use when the user wants to "extract/read/get the text
  from this image/scan/screenshot/photo/PDF", "OCR this", "image to text",
  "transcribe handwriting", "pull the text out of a picture", "read a receipt/
  form/document", or "turn an equation image into LaTeX". Covers the one-line
  call, choosing/installing a backend, reading the result (text + boxes +
  confidence), languages, and the `ocracy` CLI. For *picking* the best engine
  for a need, see ocracy-choose-backend; for *adding* a new engine, see
  ocracy-add-backend.
---

# Reading text from images with ocracy

`ocracy` turns "read the text in this image" into one call that works the same
across many OCR engines. Pick a backend once; your code doesn't change when you
switch engines.

## The one-liner

```python
import ocracy

text = ocracy.read_text("scan.png")          # -> str, default (first installed) backend
result = ocracy.ocr("scan.png")              # -> OcrResult (text + structure)
print(result)                                 # str(result) is the text
```

`image` can be a **path, an http(s) URL, raw bytes, a PIL image, or a numpy array**.

## Choosing a backend (quick guide)

`import ocracy` is dependency-free; install only the backend you use, then pass
`backend=`:

| Need | Backend | Install |
|---|---|---|
| Local, free, simple printed text | `tesseract` (default) | `pip install "ocracy[tesseract]"` (+ system `tesseract`) |
| Local, free, many scripts / scene text | `easyocr` or `rapidocr` | `pip install "ocracy[easyocr]"` / `"ocracy[rapidocr]"` |
| Local, top accuracy / CJK | `paddleocr` | `pip install "ocracy[paddleocr]"` |
| macOS, free, on-device, handwriting | `ocrmac` | `pip install "ocracy[ocrmac]"` |
| High-accuracy cloud + handwriting | `google-vision` | `pip install "ocracy[google-vision]"` |
| Forms/tables/key-value (cloud) | `aws-textract` / `azure-document-intelligence` | `"ocracy[aws-textract]"` / `"ocracy[azure]"` |
| Math/formulas → LaTeX | `mathpix` (cloud) or `pix2tex-latex-ocr` (local) | `"ocracy[mathpix]"` / `"ocracy[pix2tex]"` |
| Messy/handwritten + reasoning/extraction | `claude-vision` / `gpt-4o-vision` | `"ocracy[anthropic]"` / `"ocracy[openai]"` |

```python
result = ocracy.ocr("photo.jpg", backend="easyocr", languages=["en", "fr"])
ocracy.list_backends()          # what's installed/implemented right now
```

If the chosen backend's dependency is missing, ocracy raises a clear
`pip install ...` error. If a *remote* backend's credential is missing, the error
tells you which env var to set and links where to get a key.

For heavier setups — Paddle's framework, Torch engines, Tesseract's *system*
binary, GPU wheels, first-run model weights — use the install helpers:
`ocracy.doctor()` (what's usable now), `ocracy.requirements("paddleocr").instructions()`
(the exact OS-aware plan), `ocracy.install("rapidocr", yes=True)` (run it + verify),
or the **ocracy-install-backend** skill.

## Reading the result

Every backend returns the same `OcrResult`:

```python
result.text                 # full text, reading order
for line in result:         # iterate TextBlocks (lines by default)
    print(line.text, line.bbox.as_tuple if line.bbox else None, line.confidence)
result.words                # word-level blocks (when the engine provides them)
result.mean_confidence      # average confidence in 0..1, or None
result.markdown             # Markdown rendering (VLM/Mathpix/Mistral), else None
result.raw                  # the untouched engine output, for power users
result.filter_confidence(0.5)   # drop low-confidence blocks
```

Note: VLM and math backends (`claude-vision`, `gpt-4o-vision`, `mathpix`,
`mistral-ocr`, `pix2tex-latex-ocr`) are text/Markdown-oriented — they typically
return no bounding boxes or confidences. Use `result.text` / `result.markdown`.

## Languages

Pass ISO-639-1 codes; ocracy translates them to each engine's convention:

```python
ocracy.read_text("doc.png", backend="tesseract", languages=["en", "fr"])  # -> Tesseract "eng+fra"
ocracy.read_text("doc.png", backend="easyocr", languages=["en", "zh"])    # -> EasyOCR ["en", "ch_sim"]
```

## Remote backends need a key

```python
# Set the env var first (the error tells you which one + where to get it):
#   export OCR_SPACE_API_KEY=...        (free key: https://ocr.space/ocrapi/freekey)
#   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json
#   export MATHPIX_APP_ID=... MATHPIX_APP_KEY=...
text = ocracy.read_text("invoice.png", backend="google-vision")
```
See `ocracy.credentials.CREDENTIAL_GUIDANCE` (and the README) for every backend's
env var(s) and signup link.

## Three tiers of control

```python
ocracy.ocr(img)                                  # 1. facade, default backend
ocracy.services.tesseract.read(img, psm=6)       # 2. pick a backend, pass native-ish opts
ocracy.services.tesseract.adapter                # 3. the raw engine adapter
```

## From the shell

```bash
pip install "ocracy[cli]"
ocracy read scan.png                       # print text
ocracy read scan.png --backend easyocr --languages en,fr
ocracy read scan.png --output json         # text + blocks (boxes, confidence)
ocracy backends                            # what's installed
```

## PDFs

ocracy reads *images*. For PDFs, render pages to images first (e.g. via `pdf2image`
or the user's `pdfdol`) and OCR each page, or use a cloud document backend
(`azure-document-intelligence`, `aws-textract`, `mistral-ocr`) that accepts page
images. Concatenate `result.text` across pages.

## Gotchas
- `import ocracy` never needs an engine — installs are per-backend extras.
- The default backend is the first *installed* implemented one; pass `backend=`
  to be explicit.
- Low accuracy on a noisy scan? Preprocess (deskew, increase DPI/contrast) or
  switch to a stronger backend (`paddleocr`, a cloud API, or a VLM).
