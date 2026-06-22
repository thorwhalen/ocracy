# ocracy

One façade over many OCR engines — plus a **ledger** to help you choose between them.

OCR ("read the text in this image") is solved a dozen ways: local engines
(Tesseract, EasyOCR, PaddleOCR), cloud APIs (Google Vision, AWS Textract, Azure),
and VLM readers — each with its own install, API, pricing, and language coverage.
`ocracy` gives you a uniform call, a browsable catalog of every option, and the
tools to wrap any of them.

```python
import ocracy

text = ocracy.read_text("scan.png")          # just the text, default backend
result = ocracy.ocr("scan.png")              # full result: text + word boxes + confidence
print(result)                                # -> the recognized text
for word in result.words:
    print(word.text, word.bbox.as_tuple, word.confidence)
```

## Install

`import ocracy` is dependency-free. Install only the backends you use, via extras:

```bash
pip install "ocracy[tesseract]"     # local, free (also needs the system `tesseract` binary)
pip install "ocracy[easyocr]"       # local, pip-only
pip install "ocracy[google-vision]" # cloud API
pip install "ocracy[table]"         # pandas, for catalog.to_dataframe()
```

## Backends that ship today

| Backend | `backend=` id | Local / Remote | Cost | Install | Notable |
|---|---|---|---|---|---|
| Tesseract | `tesseract` | local | free | `ocracy[tesseract]` (+ system `tesseract`) | 100+ language baseline |
| EasyOCR | `easyocr` | local | free | `ocracy[easyocr]` | 80+ languages, scene text |
| RapidOCR | `rapidocr` | local | free | `ocracy[rapidocr]` | same PP-OCR models as Paddle, light CPU/ONNX — **recommended default for local plain text** |
| PaddleOCR | `paddleocr` | local | free | `ocracy[paddleocr]` | the platform: server models, GPU, on-ramp to tables/layout (PP-Structure) & VL — heavier install |
| ocrmac (Apple Vision) | `ocrmac` | local (macOS) | free | `ocracy[ocrmac]` | on-device, handwriting |
| OCR.space | `ocr-space` | remote | free tier | `ocracy[ocr-space]` | zero-install REST |
| Google Cloud Vision | `google-vision` | remote | paid (+free tier) | `ocracy[google-vision]` | high accuracy, handwriting, structure |
| AWS Textract | `aws-textract` | remote | paid (+free tier) | `ocracy[aws-textract]` | business docs, handwriting (forms/tables in analyze mode) |
| Azure Document Intelligence | `azure-document-intelligence` | remote | paid (+free tier) | `ocracy[azure]` | layout/tables/handwriting, on-prem container option |
| Mistral OCR | `mistral-ocr` | remote | paid (pay-as-you-go) | `ocracy[mistral]` | cheap VLM → clean Markdown + math/tables |
| Mathpix | `mathpix` | remote | paid (+free tier) | `ocracy[mathpix]` | math/handwriting → LaTeX & Markdown |

…plus **53 more** engines/services catalogued in the ledger that you can turn into
a working façade with one command (see *Add a backend* below).

### Getting a backend running

Some backends need more than `pip install` (Tesseract's *system* binary, Paddle's
framework, GPU wheels, first-run model weights, or an API key). ocracy turns that
into structured, OS-aware guidance — handy for humans and AI agents alike:

```python
ocracy.doctor()                       # what's usable now vs what each missing one needs
ocracy.check("paddleocr")             # -> True/False (usable right now?)
print(ocracy.requirements("paddleocr").instructions())   # exact plan: pip + system deps + GPU + weights
ocracy.install("rapidocr", yes=True)  # run the pip install + verify (yes=False = dry run)
```
```bash
ocracy doctor · ocracy requirements paddleocr --gpu · ocracy install rapidocr --yes
```
`requirements()` even suggests a *lighter alternative* when one exists (e.g.
PaddleOCR → RapidOCR). The `ocracy-install-backend` skill drives all of this.

## Three tiers of access

From simplest to most powerful — reach for the next tier only when you need it:

```python
ocracy.ocr(img)                                    # 1. facade, default (installed) backend
ocracy.ocr(img, backend="easyocr", languages=["en", "fr"])
ocracy.services.tesseract.read(img, psm=6)         # 2. pick a backend explicitly
ocracy.services.tesseract.adapter                  # 3. the raw engine adapter, full control
```

Every backend returns the same `OcrResult`, so your code doesn't change when you
switch engines: `result.text`, `result.words` / `result.lines`, each block's
`.bbox` and `.confidence` (normalized to 0..1), `result.mean_confidence`,
`result.markdown` (when a backend produces it), and `result.raw` (the untouched
engine output).

## Command line

Install the CLI extra (`pip install "ocracy[cli]"`) for an `ocracy` command:

```bash
ocracy read scan.png                          # print recognized text
ocracy read scan.png --backend easyocr --languages en,fr
ocracy read scan.png --output json            # text + blocks (boxes, confidence)
ocracy backends                               # backends you can run now
ocracy backends --capability math
ocracy status                                 # readiness table: all / implemented / set-up / tested
ocracy status --level set_up --names          # one level + the "Name (website)" lists
ocracy status --run-tests                     # also OCR-test set-up backends (real calls for remotes)
ocracy find --local --free --handwriting      # browse/filter the ledger
ocracy info google-vision                     # a backend's full record
ocracy scaffold surya                          # start a new façade from the ledger
ocracy validate tesseract                      # smoke-test a backend
```

Everything is also reachable as `python -m ocracy <command>`. `argh` builds the
parser from the function signatures in `ocracy/tools.py`; `argcomplete` gives tab
completion when activated.

## The ledger — choose a backend with eyes open

`ocracy` ships a curated, data-driven catalog of **every** engine we researched —
not only the ones with a working façade — so you can compare on the axes that
matter (local vs remote, price, accuracy, languages, handwriting, math, tables,
privacy). The data lives in `ocracy/data/backends.json`, separate from code.

```python
ocracy.catalog                                       # <Catalog … backends … implemented …>
ocracy.catalog["google-vision"]                      # one backend's full record
ocracy.find(is_local=True, open_source=True)         # filter the ledger
ocracy.find(handwriting="yes", is_remote=True)
ocracy.catalog.can("math")                           # engines that read formulas
ocracy.catalog.supports_language("Arabic")
ocracy.find(implemented=True)                         # only what ocracy can run today
ocracy.catalog.to_dataframe()                         # browse as a pandas table
ocracy.catalog.compare(["tesseract", "google-vision", "mathpix"])
```

`implemented` is computed live from the code, so the ledger never lies about what
actually runs. See `ocracy/data/SCHEMA.md` for every field. The full cited research
report behind the ledger is in [`misc/docs/ocr_landscape_research.md`](misc/docs/ocr_landscape_research.md).

## Getting API keys (remote backends)

Remote backends need a credential in an environment variable. ocracy tells you
exactly which one — **with a link to get it** — the moment it's missing:

```python
>>> ocracy.ocr("receipt.png", backend="ocr-space")
MissingCredentialError: No credential found for ocr-space (set one of: OCR_SPACE_API_KEY).
How to get a credential for ocr-space: Register a free API key by email; free tier
allows 25,000 requests/month. Get a key: https://ocr.space/ocrapi/freekey
```

| Backend | Environment variable(s) | Where to get a key |
|---|---|---|
| `ocr-space` | `OCR_SPACE_API_KEY` | <https://ocr.space/ocrapi/freekey> (free, 25k/month) |
| `google-vision` | `GOOGLE_APPLICATION_CREDENTIALS` (service-account JSON path) | <https://cloud.google.com/vision/docs/setup> |
| `aws-textract` | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` + `AWS_DEFAULT_REGION` | <https://docs.aws.amazon.com/textract/latest/dg/getting-started.html> |
| `azure-document-intelligence` | `AZURE_DOCUMENT_INTELLIGENCE_KEY` + `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` | <https://learn.microsoft.com/azure/ai-services/document-intelligence/create-document-intelligence-resource> |
| `mistral-ocr` | `MISTRAL_API_KEY` | <https://console.mistral.ai/api-keys> |
| `mathpix` | `MATHPIX_APP_ID` + `MATHPIX_APP_KEY` | <https://mathpix.com/ocr-api> |

The same guidance (and links for AWS, Azure, Mistral, OpenAI, Anthropic, Gemini)
lives in `ocracy.credentials.CREDENTIAL_GUIDANCE`, and powers the dynamic errors.
Tip: drop the variables in a `.env` file — ocracy soft-loads it via `python-dotenv`
if that package is installed.

## Add a backend (wrap any engine in minutes)

The catalog is large; `ocracy` ships façades for a curated subset and gives you
the machinery to add any other one. Scaffold a backend straight from its ledger
entry, fill in the adapter, and validate it:

```python
from ocracy.make_backend import scaffold_backend, validate_adapter

scaffold_backend("mathpix")     # creates ocracy/backends/mathpix/ prefilled from the ledger
# ... implement adapter.py's _read (call the engine, return an OcrResult) ...
validate_adapter("mathpix")     # smoke-test it end to end
```

The full, step-by-step process — including the adapter contract, input/output
normalization helpers, credential handling, and packaging — is captured as an
agent **skill** at `ocracy/data/skills/ocracy-add-backend/SKILL.md`. The
`ocracy/backends/tesseract/` package is a complete worked example.

## Agent skills (Claude Code & other AI agents)

ocracy ships three Anthropic-style **skills** (under `ocracy/data/skills/`,
installed with the package) so AI coding agents can both *use* and *extend* it:

| Skill | Audience | What it helps with |
|---|---|---|
| `ocracy` | users | OCR an image/PDF, choose & install a backend, read the result |
| `ocracy-choose-backend` | users | filter & compare the 64-backend ledger to pick the right engine |
| `ocracy-install-backend` | users / agents | get a backend running — heavy installs, system deps, GPU, weights, keys |
| `ocracy-add-backend` | developers | wrap a new engine behind ocracy's interface (scaffold → adapter → validate) |

In a repo using Claude Code they're discoverable via the `.claude/skills/`
symlink bridge; they also travel with `pip install ocracy` under
`ocracy/data/skills/`.

## How it works

- `ocracy/base.py` — the normalized types (`OcrResult`, `TextBlock`, `BBox`).
- `ocracy/catalog.py` — the ledger reader/filter (`ocracy/data/backends.json`).
- `ocracy/registry.py` — lazy backend discovery + default selection.
- `ocracy/services.py` — the three-tier service layer.
- `ocracy/make_backend.py` — the façade-building toolkit (`BaseOcrAdapter`,
  `make_block`, `scaffold_backend`, `validate_adapter`).
- `ocracy/backends/<id>/` — one subpackage per engine (`config.py` + `adapter.py`).
- `ocracy/credentials.py` — credential resolution for remote backends.
- `ocracy/tools.py` + `ocracy/__main__.py` — the `ocracy` CLI (argh).

The architecture mirrors the sibling façade packages
[`denote`](https://github.com/thorwhalen/denote) (audio→symbol) and
[`aix`](https://github.com/thorwhalen/aix) (LLM providers).
