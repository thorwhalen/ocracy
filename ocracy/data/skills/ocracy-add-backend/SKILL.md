---
name: ocracy-add-backend
description: >-
  Build a new OCR backend façade for the ocracy package — wrap any engine or
  service (Tesseract, EasyOCR, PaddleOCR, Google Vision, AWS Textract, Mathpix,
  a VLM, ...) behind ocracy's uniform `ocr()` interface. Use when the user wants
  to "add a backend to ocracy", "wrap <engine> in ocracy", "implement an OCR
  façade", "make ocracy support <service>", pick a backend from the ledger and
  make it real, or extend ocracy's engine coverage. Walks through scaffolding
  from the ledger, filling the config/param_map, implementing the adapter's
  `_read`, normalizing output to `OcrResult`, handling credentials, packaging
  the extra, and validating end to end.
---

# Adding an OCR backend façade to ocracy

ocracy presents **one** interface — `ocracy.ocr(image, backend=...) -> OcrResult` —
over **many** OCR engines. Each engine is a small *adapter* that (1) takes
ocracy's normalized request, (2) calls the native engine, and (3) returns a
normalized `OcrResult`. This skill is the repeatable process for writing one.

The ledger (`ocracy/data/backends.json`, browse via `ocracy.catalog`) lists far
more engines than ocracy ships façades for. Turning a *listed* backend into an
*implemented* one is exactly this process.

## The contract (what "a backend" is)

A backend is a subpackage `ocracy/backends/<id>/` with two modules:

- **`config.py`** — a `BACKEND_CONFIG` dict: identity, `import_name` (for the
  availability probe), `is_local`/`is_remote`, `capabilities`, `api_env_var`
  (remote), and a **`param_map`** translating ocracy's normalized kwargs to the
  engine's native ones.
- **`adapter.py`** — an `Adapter` class with `read(image, **kwargs) -> OcrResult`.
  Subclass `ocracy.make_backend.BaseOcrAdapter` and implement `_read`; kwarg
  translation is then automatic.

The registry discovers it automatically (no registration code needed). A backend
named with a leading `_` (like `_template`) is ignored.

## Process

### 1. Pick the backend and read its ledger entry
```python
import ocracy

ocracy.find(is_local=True, open_source=True)  # explore options
info = ocracy.catalog["easyocr"]  # the record you'll implement
info.python_install, info.languages_note, info.api_env_var
```
Decide the **id** (kebab-case, matches the ledger id, e.g. `google-vision`).

### 2. Scaffold from the ledger
```python
from ocracy.make_backend import scaffold_backend

scaffold_backend("easyocr")  # -> ocracy/backends/easyocr/ (config prefilled)
```
The on-disk module uses underscores (`google_vision`), the config `id` keeps the
hyphen (`google-vision`). Pass `dest=` to scaffold elsewhere, `overwrite=True` to
replace.

### 3. Fill `config.py`
- Set `import_name` to the module used to probe availability (e.g. `easyocr`).
- Set `is_local`/`is_remote`, and `capabilities` for anything beyond plain
  `read` (`"tables"`, `"math"`, `"handwriting"`, `"layout"`, `"barcodes"`).
- Set `default_for: ["read"]` only if this should be a default engine.
- For remote backends set `api_env_var` (e.g. `"MISTRAL_API_KEY"`).
- **`param_map`** is the heart of it — map ocracy's normalized names to native:
  ```python
  "param_map": {
      "languages": {"native_name": "lang", "coerce": _to_native_langs},
      "psm": {"native_name": "psm"},
      "detect_orientation": None,    # explicitly unsupported -> warns if passed
  }
  ```
  `coerce` is a callable (define it in `config.py`); `default` injects a value
  when the caller omits the param. Keep ocracy's vocabulary stable across engines
  (prefer `languages`, not each engine's spelling).

### 4. Implement `adapter.py`'s `_read`
Three jobs, in order:
```python
from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    def _read(self, image, **native_kwargs) -> OcrResult:
        import the_engine  # 1. LAZY import (never at module top)
        from ocracy.util import to_pil, ensure_file_path, cleanup_temp, load_image_bytes

        pil = to_pil(image)  # 2. normalize input to what the engine wants
        native = the_engine.run(pil, **native_kwargs)

        blocks = [  # 3. normalize output
            make_block(
                w.text, bbox=w.box, confidence=w.score, conf_scale=1.0, level="word"
            )
            for w in native.words
        ]
        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=native)
```
Input helpers (`ocracy.util`): `to_pil`, `to_numpy`, `load_image_bytes` (REST
APIs), `ensure_file_path`/`cleanup_temp` or the `image_path` context manager
(engines wanting a path). **Always** keep the native response in `raw=`.

Output helpers (`ocracy.make_backend`): `make_block(text, bbox=…, confidence=…,
conf_scale=…, level=…)` builds a normalized `TextBlock` (rescales confidence to
0..1 — use `conf_scale=100` for percent engines; accepts `(x0,y0,x1,y1)` tuples
or polygons for `bbox`). Assemble with `OcrResult.from_blocks(...)` (synthesizes
reading-order text if you don't pass `text=`) or `OcrResult.from_text(...)` for
text-only engines (VLMs). Put a Markdown rendering in `meta["markdown"]` if the
engine returns one.

### 5. Credentials (remote backends only)
```python
from ocracy.credentials import resolve_credential

key = resolve_credential(
    self.backend_id,
    api_key=native_kwargs.pop("api_key", None),
    env_var=self.config.get("api_env_var"),
)
```
Never hardcode keys; let the env var / `.env` resolve them.

### 6. Package the extra
Add to `pyproject.toml` `[project.optional-dependencies]`:
```toml
easyocr = ["easyocr>=1.7"]
```
so users can `pip install "ocracy[easyocr]"`.

### 7. Make sure it's in the ledger
If the id isn't in `ocracy/data/backends.json`, add a record (see
`ocracy/data/SCHEMA.md`). `implemented` is computed live — no need to set it.

### 8. Validate + test
```python
from ocracy.make_backend import validate_adapter

validate_adapter(
    "easyocr"
)  # {available, ran, ok, returns_ocrresult, text, n_blocks, ...}
```
Add a dependency-gated test under `tests/` (skip if the engine/SDK or creds are
missing) modeled on `tests/test_make_backend.py`.

## Gotchas
- **Lazy imports**: import the engine *inside* `_read`, never at module top —
  `import ocracy` must stay dependency-free.
- **Confidence scale**: normalize to 0..1 (`conf_scale=100` for 0..100 engines).
- **Reading order**: pass blocks in reading order, or pass an explicit `text=`.
- **Temp files**: if you wrote one with `ensure_file_path`, clean it up
  (`cleanup_temp`) or use the `image_path` context manager.
- **Module name vs id**: directory uses underscores; `config["id"]` keeps hyphens.
- **Don't break the facade vocabulary**: reuse normalized param names across
  engines so `ocracy.ocr(img, languages=[...])` means the same thing everywhere.

## Worked example
`ocracy/backends/tesseract/` is a complete, real reference: `param_map` with a
`languages -> lang` coercion, `_read` mapping Tesseract's TSV word rows into
`TextBlock`s with rescaled confidence, and reading-order text assembly.
