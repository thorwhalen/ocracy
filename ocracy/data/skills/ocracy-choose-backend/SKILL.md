---
name: ocracy-choose-backend
description: >-
  Choose or compare OCR engines/services using ocracy's data-driven ledger (64
  researched backends). Use when the user asks "which OCR should I use", "what's
  the best OCR for <language / handwriting / math / tables / receipts>", "compare
  OCR engines/services", "local vs cloud OCR", "cheapest OCR API", "free offline
  OCR", "OCR options", or wants to weigh accuracy / price / privacy / language
  coverage before committing to a backend. Filters the ledger by feature and
  explains the trade-offs. For actually running OCR see ocracy; for adding a new
  engine see ocracy-add-backend.
---

# Choosing an OCR backend with ocracy's ledger

ocracy ships a **ledger** — a researched, filterable catalog of 64 OCR
engines/services (`ocracy/data/backends.json`) covering local + remote, free +
paid, and beyond-plain-text (math, tables, handwriting). Use it to pick with eyes
open instead of guessing.

## Filter the ledger

```python
import ocracy

ocracy.catalog  # <Catalog 64 backends | … implemented …>
ocracy.find(is_local=True, open_source=True)  # local, free engines
ocracy.find(is_remote=True)  # hosted APIs
ocracy.find(implemented=True)  # only what ocracy can run today
ocracy.catalog.can("math")  # engines that read formulas
ocracy.catalog.can("tables")  # ... tables
ocracy.catalog.can("handwriting")  # ... handwriting
ocracy.catalog.supports_language("Arabic")  # languages_note mentions Arabic
ocracy.find(is_local=True).can("handwriting")  # filters compose (AND)
```

Inspect and compare:

```python
ocracy.catalog["google-vision"]  # one backend's full record
ocracy.catalog["google-vision"].to_dict()  # raw fields (price, accuracy, langs, ...)
ocracy.catalog.compare(["tesseract", "google-vision", "mathpix"])  # side-by-side
ocracy.catalog.to_dataframe()  # browse as a pandas table (pip install "ocracy[table]")
```

From the shell: `ocracy find --local --free --handwriting`, `ocracy info <id>`.

## The axes that matter

- **Local vs remote** — privacy / offline / no per-call cost (local) vs zero-ops
  scale and frontier accuracy (remote). Some backends are both.
- **Pricing** — `free_oss`, `freemium`, `free_tier_then_paid`, `pay_as_you_go`,
  `subscription`, `proprietary_quote`. Read `price_note` / `free_tier`.
- **Accuracy** — `accuracy_tier` + `accuracy_note` (benchmark numbers where they
  exist, e.g. OmniDocBench/OCRBench/CER).
- **Languages / scripts** — `languages_count` + `languages_note` (script families
  matter more than the raw count; handwriting coverage is a narrower subset).
- **Beyond text** — `handwriting`, `math_formula`, `tables`, `layout_structure`,
  and the `beyond_text` list (barcodes, music, key_value, charts, ...).
- **Output** — `output_formats`, `bounding_boxes`, `confidence_scores`. Note:
  VLM/math backends usually give text/Markdown but no boxes/confidence.
- **Privacy / GPU / maturity** — `privacy_note`, `gpu_recommended`, `maturity_note`.

## Quick recommendations

- **Local + free, just works:** `tesseract` (printed, 100+ langs); `rapidocr`
  (**recommended light default** — same PP-OCR models as Paddle, CPU-only, trivial
  install); `paddleocr` (the *platform* — pick it over rapidocr only when you need
  the larger server models, GPU throughput, fine-tuning, or to grow into
  PP-Structure tables/layout/formula or PaddleOCR-VL); `easyocr` (scene text);
  `ocrmac` (macOS, on-device, handwriting).
- **Cloud, high accuracy:** `google-vision` (general + handwriting),
  `azure-document-intelligence` / `aws-textract` (forms/tables/layout),
  `mistral-ocr` (cheap modern VLM → Markdown).
- **Math/formulas:** `mathpix` (cloud, best-in-class) or `pix2tex-latex-ocr`
  (local, free).
- **Messy / handwritten / structured extraction:** a VLM (`claude-vision`,
  `gpt-4o-vision`) when you want "read + reason", not just a transcript.

## Implemented vs listed

The `implemented` flag (computed live from the code) tells you which backends
ocracy can run *today* vs which are catalogued but not yet wrapped. To turn a
listed backend into a working one, see the **ocracy-add-backend** skill. The full
cited research behind the ledger is in `misc/docs/ocr_landscape_research.md`.

Once you've chosen, hand off to the **ocracy** skill to actually run it
(`ocracy.ocr(image, backend="<id>")`).
