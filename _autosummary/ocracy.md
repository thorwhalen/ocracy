# ocracy

ocracy — one facade over many OCR engines, plus a ledger to choose between them.

OCR (“read the text in this image”) is solved a dozen different ways: local
engines (Tesseract, EasyOCR, PaddleOCR), cloud APIs (Google Vision, AWS
Textract, Azure), and VLM-based readers — each with its own install, API,
pricing, language coverage, and quirks. ocracy gives you:

1. **A uniform facade.** Call [`ocr()`](#ocracy.ocr) and get the same [`OcrResult`](ocracy.base.md#ocracy.base.OcrResult)
   back no matter which backend ran:
   ```default
   import ocracy
   result = ocracy.ocr("scan.png")          # default (first installed) backend
   print(result)                            # -> the recognized text
   result = ocracy.ocr("scan.png", backend="easyocr", languages=["en", "fr"])
   ```

   Convenience: [`read_text()`](#ocracy.read_text) returns just the string.
2. **A ledger / gallery** of *every* engine we researched — not only the ones
   with a working facade — so you can choose with eyes open:
   ```default
   ocracy.catalog                                   # the whole ledger
   ocracy.find(is_local=True, open_source=True)     # filter it
   ocracy.find(handwriting="yes", is_remote=True)
   ocracy.catalog.to_dataframe()                    # browse as a table
   ```

   The ledger lives in data (`ocracy/data/backends.json`), not code.
3. **Tools to build new facades.** The catalog is large; ocracy ships a facade
   for a curated subset and gives you the machinery (and a SKILL) to add any
   other one in minutes:
   ```default
   from ocracy.make_backend import scaffold_backend, validate_adapter
   scaffold_backend("mathpix")    # generate a backend package from the ledger
   validate_adapter("tesseract")  # smoke-test an adapter end to end
   ```

Three tiers of access, from simplest to most powerful:

```default
ocracy.ocr(img)                                # facade, default backend
ocracy.services.tesseract.read(img, lang="fra")  # pick a backend
ocracy.services.tesseract.adapter              # raw engine adapter
```

### Module Attributes

| [`services`](#ocracy.services)   | Singleton service collection for per-backend access (`services.tesseract`).   |
|-------------------------------------------------------------|-------------------------------------------------------------------------------|

### Functions

| [`ocr`](#ocracy.ocr)(image, \*[, backend])                        | Read text from an image with any backend, returning a normalized result.                                  |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|
| [`read_text`](#ocracy.read_text)(image, \*[, backend])                  | Like [`ocr()`](#ocracy.ocr) but returns just the recognized text string.  |
| [`find`](#ocracy.find)(\*\*criteria)                               | Filter the ledger; shorthand for `ocracy.catalog.Catalog.filter()`.                                       |
| [`list_backends`](#ocracy.list_backends)([capability])                      | Sorted ids of implemented backends, optionally filtered by capability.                                    |
| [`register_backend`](#ocracy.register_backend)(backend_id, config[, adapter])  | Register a backend at runtime (for third-party plugins).                                                  |
| [`get_default_backend`](#ocracy.get_default_backend)([capability, ...])           | Pick a sensible default backend id for a capability.                                                      |
| [`get_config`](#ocracy.get_config)(backend_id)                           | A backend's `BACKEND_CONFIG` without loading its adapter.                                                 |
| [`make_block`](#ocracy.make_block)(text, \*[, bbox, confidence, ...])    | Build a normalized [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock).      |
| [`scaffold_backend`](#ocracy.scaffold_backend)(backend_id, \*[, dest, ...])    | Create a new `ocracy/backends/<id>/` package from the template.                                           |
| [`validate_adapter`](#ocracy.validate_adapter)(backend_id, \*[, image, ...])   | Smoke-test a backend adapter end to end, returning a report dict.                                         |
| [`requirements`](#ocracy.requirements)(backend_id, \*[, gpu])              | Return structured install [`Requirements`](#ocracy.Requirements) for `backend_id`. |
| [`check`](#ocracy.check)(backend_id)                                | Is `backend_id` importable / usable right now? (no install, no network).                                  |
| [`doctor`](#ocracy.doctor)()                                         | Report which implemented backends are usable now and what the rest need.                                  |
| [`install`](#ocracy.install)(backend_id, \*[, yes, gpu, verify, ...]) | Plan (and optionally run) the pip install for a backend.                                                  |
| [`available_backends`](#ocracy.available_backends)()                             | Implemented backends whose dependency is importable right now.                                            |
| [`backend_ids`](#ocracy.backend_ids)([level, info, test_image])           | Sorted backend ids at a readiness `level` (one of `LEVELS`).                                              |
| [`backend_info`](#ocracy.backend_info)([ids, run_tests, test_image])       | Per-backend status: every ledger field plus `implemented`/`set_up`/`tested`.                              |
| [`status_table`](#ocracy.status_table)([ids, info, columns, ...])          | Render an aligned Markdown table of backend status (also plain-text readable).                            |
| [`names_with_sites`](#ocracy.names_with_sites)(ids, \*[, info])                | `"Name (website), Name2 (website2), ..."` for `ids` (name, not id).                                       |
| [`is_set_up`](#ocracy.is_set_up)(backend_id)                            | Ready to run here & now.                                                                                  |
| [`is_tested`](#ocracy.is_tested)(backend_id, \*[, image])               | Actually run OCR on `image` (a generated one if None); True iff it worked.                                |

### Classes

| [`OcrResult`](#ocracy.OcrResult)(text[, blocks, backend, raw, meta])     | The normalized result of reading an image with any backend.                                                      |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| [`TextBlock`](#ocracy.TextBlock)(text[, bbox, confidence, level, ...])   | One recognized unit of text.                                                                                     |
| [`BBox`](#ocracy.BBox)(x0, y0, x1, y1[, polygon])                   | An axis-aligned bounding box in pixel coordinates (origin = top-left).                                           |
| [`BackendInfo`](#ocracy.BackendInfo)(record, \*[, implemented])            | One backend's ledger entry — a read-only, attribute-and-dict accessible record.                                  |
| [`Catalog`](#ocracy.Catalog)([path, \_records])                        | A filterable, dict-like collection of [`BackendInfo`](#ocracy.BackendInfo), keyed by id. |
| [`ServiceCollection`](#ocracy.ServiceCollection)()                               | Lazy mapping of backend ids -> `ServiceHandle`.                                                                  |
| [`BaseOcrAdapter`](#ocracy.BaseOcrAdapter)(config)                            | Optional base class for backend adapters.                                                                        |
| [`Requirements`](#ocracy.Requirements)(backend_id, implemented, ...[, ...]) | What a backend needs to run — structured for an agent to act on.                                                 |

### *class* ocracy.BBox(x0, y0, x1, y1, polygon=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

An axis-aligned bounding box in pixel coordinates (origin = top-left).

`polygon` optionally carries the original (possibly rotated) vertices as a
sequence of `(x, y)` points; the axis-aligned `x0/y0/x1/y1` are always
populated (derived from the polygon if a backend only gives one).

#### *property* as_tuple *: [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple)[[float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float)]*

`(x0, y0, x1, y1)` — the convention PIL’s `crop` expects.

#### *classmethod* from_polygon(points)

Build a box from polygon vertices `[(x, y), ...]`.

The axis-aligned extent is computed from the vertices and the original
polygon is preserved for callers that care about rotation.

* **Return type:**
  [`BBox`](ocracy.base.md#ocracy.base.BBox)

#### *property* xywh *: [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple)[[float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float)]*

`(x, y, width, height)` — the convention many drawing libs expect.

### *class* ocracy.BackendInfo(record, , implemented=False)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)

One backend’s ledger entry — a read-only, attribute-and-dict accessible record.

Wraps the raw record dict so that new fields added to the JSON are available
immediately (via attribute or key access) without code changes, while a few
commonly used fields get typed properties for convenience and discoverability.

### *class* ocracy.BaseOcrAdapter(config)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Optional base class for backend adapters.

Stores the config, builds a kwarg translator from `config['param_map']`,
and implements `read` as: translate normalized kwargs -> native kwargs ->
`_read()`. Subclasses implement `_read()` and return an
[`OcrResult`](ocracy.base.md#ocracy.base.OcrResult).

Adapters are not *required* to subclass this — the registry only needs an
`Adapter` class with a `read(image, **kwargs)` method — but doing so
removes the boilerplate.

### *class* ocracy.Catalog(path=None, , \_records=None)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)

A filterable, dict-like collection of [`BackendInfo`](#ocracy.BackendInfo), keyed by id.

Loaded lazily from `DEFAULT_LEDGER_PATH` (override via the `path`
argument or the `OCRACY_LEDGER` environment variable). [`filter()`](#ocracy.Catalog.filter)
returns a *new* `Catalog` over the matching subset, so filters compose:

```default
catalog.filter(is_remote=True).filter(pricing_model="free_tier_then_paid")
```

#### can(capability)

Backends with a non-plain-text `capability` (e.g. `"math"`, `"tables"`).

Matches either the `beyond_text` list or a `<capability>` field set
to `"yes"` (e.g. `handwriting`, `tables`, `math_formula`).

* **Return type:**
  [`Catalog`](#ocracy.Catalog)

#### compare(ids=None, , fields=('name', 'is_local', 'is_remote', 'open_source', 'pricing_model', 'price_note', 'accuracy_tier', 'languages_count', 'handwriting', 'math_formula', 'tables', 'best_for'))

A trimmed, side-by-side view of selected backends and fields.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### filter(, predicate=None, implemented=None, \*\*criteria)

Return a new `Catalog` of backends matching every criterion.

* **Parameters:**
  * **predicate** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`BackendInfo`](#ocracy.BackendInfo)], [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]]) – An arbitrary `BackendInfo -> bool` callable.
  * **implemented** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]) – If set, keep only (un)implemented backends.
  * **\*\*criteria** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – `field=value` constraints. `value` may be a
    set/list/tuple meaning “one of”. Free-text fields
    (`languages_note`, `beyond_text`, `output_formats`) use a
    case-insensitive substring match.
* **Return type:**
  [`Catalog`](#ocracy.Catalog)

Example:

```default
catalog.filter(is_local=True, open_source=True, handwriting="yes")
```

#### supports_language(language)

Backends whose `languages_note` mentions `language` (name or code).

* **Return type:**
  [`Catalog`](#ocracy.Catalog)

#### to_dataframe(, columns=None)

Return a pandas DataFrame of the catalog (pandas imported lazily).

### *class* ocracy.OcrResult(text, blocks=<factory>, backend='', raw=None, meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The normalized result of reading an image with any backend.

`text` is the headline payload: the full recognized text in reading order.
`blocks` carries the structured units (with boxes/confidences) when the
backend provides them. `raw` is the untouched backend output. `meta`
holds cross-cutting extras (languages, page count, a Markdown rendering,
timing, …).

Progressive disclosure:

```default
result = ocracy.ocr("scan.png")
print(result)              # -> the text
result.text                # -> the same string
for line in result:        # -> iterate TextBlocks (lines by default)
    print(line.text, line.confidence)
result.words               # -> only word-level blocks
result.mean_confidence     # -> average confidence, if available
result.raw                 # -> engine-specific structure
```

#### at_level(level)

Blocks at a given granularity (`"word"`, `"line"`, …).

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`TextBlock`](ocracy.base.md#ocracy.base.TextBlock)]

#### filter_confidence(min_confidence)

Return a copy keeping only blocks at or above `min_confidence`.

Blocks without a confidence are dropped. `text` is rebuilt from the
surviving blocks (joined by newline).

* **Return type:**
  [`OcrResult`](ocracy.base.md#ocracy.base.OcrResult)

#### *classmethod* from_blocks(blocks, , backend='', raw=None, text=None, joiner='\\\\n', \*\*meta)

Build a result from structured blocks.

If `text` is not given it is synthesized by joining the blocks’ text in
their given order with `joiner` (callers should pass blocks already in
reading order, or pre-join and pass `text` explicitly).

* **Return type:**
  [`OcrResult`](ocracy.base.md#ocracy.base.OcrResult)

#### *classmethod* from_text(text, , backend='', raw=None, \*\*meta)

Build a minimal result from just a text string (no geometry).

* **Return type:**
  [`OcrResult`](ocracy.base.md#ocracy.base.OcrResult)

#### *property* markdown *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Markdown rendering if the backend produced one (else `None`).

#### *property* mean_confidence *: [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Mean confidence over blocks that report one, or `None`.

### *class* ocracy.Requirements(backend_id, implemented, available, is_local, is_remote, pip_command, extra=None, system=<factory>, system_note=None, gpu=None, weights=None, heavy=False, alternative=None, credentials=<factory>, notes=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What a backend needs to run — structured for an agent to act on.

#### instructions()

An agent-/human-readable, copy-pasteable install plan.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* ocracy.ServiceCollection

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)

Lazy mapping of backend ids -> `ServiceHandle`.

Supports dict-style (`services['tesseract']`) and attribute-style
(`services.tesseract`) access.

### *class* ocracy.TextBlock(text, bbox=None, confidence=None, level='line', language=None, meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One recognized unit of text.

#### text

The recognized string for this unit.

#### bbox

Where it was found (pixel coordinates), if the backend reports it.

#### confidence

Recognition confidence in `[0, 1]` (normalized by ocracy
from whatever scale the backend used), if available.

#### level

Granularity — one of `ocracy.base.LEVELS` (“word”, “line”, …).

#### language

Detected/declared language code for this unit, if any.

#### meta

Backend-specific extras (font size, style, page index, …).

### ocracy.available_backends()

Implemented backends whose dependency is importable right now.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ocracy.backend_ids(level='all', , info=None, test_image=None)

Sorted backend ids at a readiness `level` (one of `LEVELS`).

Pass a precomputed `info` (from [`backend_info()`](#ocracy.backend_info)) to avoid recomputation
— important for `"tested"`, which otherwise re-runs OCR.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ocracy.backend_info(ids=None, , run_tests=False, test_image=None)

Per-backend status: every ledger field plus `implemented`/`set_up`/`tested`.

* **Parameters:**
  * **ids** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]) – Which backends (default: every ledger id).
  * **run_tests** – Which set-up backends to actually OCR-test. `True` = all
    set-up (real API calls for remotes!); `False` = none (`tested` is
    `None`); or an iterable of ids to limit testing to those.
  * **test_image** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Image to test with (default: a generated one, shared across all).
* **Return type:**
  [`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]
* **Returns:**
  `{id: {..., "name", "website", "implemented", "set_up", "tested"}}` where
  `tested` is `True`/`False`/`None` (None = not attempted).

### ocracy.check(backend_id)

Is `backend_id` importable / usable right now? (no install, no network).

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.doctor()

Report which implemented backends are usable now and what the rest need.

Returns `{"available": [...], "missing": {id: one-line install hint}}`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.find(\*\*criteria)

Filter the ledger; shorthand for `ocracy.catalog.Catalog.filter()`.

Example:

```default
ocracy.find(is_local=True, open_source=True, handwriting="yes")
ocracy.find(implemented=True)        # only backends ocracy can run now
```

* **Return type:**
  [`Catalog`](#ocracy.Catalog)

### ocracy.get_config(backend_id)

A backend’s `BACKEND_CONFIG` without loading its adapter.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.get_default_backend(capability='read', , require_available=True)

Pick a sensible default backend id for a capability.

Strategy (OCR-tuned): prefer a backend explicitly flagged `default_for` the
capability *and* whose dependency is importable; then any importable backend
for the capability; then — if `require_available` is False or nothing is
installed — the first registered candidate (using it will raise a helpful
install error).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.install(backend_id, , yes=False, gpu=False, verify=True, upgrade=False)

Plan (and optionally run) the pip install for a backend.

With `yes=False` (default) this is a **dry run**: it returns the plan
without changing anything — call `result['requirements'].instructions()` to
show it. With `yes=True` it runs `pip install` for the backend’s extra in
the current interpreter, then (if `verify`) checks importability.

System dependencies and GPU wheels are *surfaced*, never run automatically
(they need sudo/brew or an environment-specific CUDA choice) — run those
yourself from `result['requirements'].system` / `.gpu`.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.is_set_up(backend_id)

Ready to run here & now.

Requires the engine/client to be importable (local *and* remote), and — for a
remote backend — its (primary) credential env var to resolve. So a remote
whose key is set but whose client library isn’t installed is *not* set up
(it couldn’t actually run). Returns False for ledger-only backends.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.is_tested(backend_id, , image=None)

Actually run OCR on `image` (a generated one if None); True iff it worked.

For remote backends this performs a real API call. Returns False if the
backend isn’t set up or the run fails.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.list_backends(capability=None)

Sorted ids of implemented backends, optionally filtered by capability.

A backend matches `capability` if it appears in the backend’s
`capabilities` list (the primary `"read"` is implied for all).

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ocracy.make_block(text, , bbox=None, confidence=None, conf_scale=1.0, level='word', language=None, \*\*meta)

Build a normalized [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock).

`bbox` may be any shape accepted by `as_bbox()`. `confidence` is
normalized to `[0, 1]` via `conf_scale` (e.g. `conf_scale=100` for
percent-scale engines).

* **Return type:**
  [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock)

### ocracy.names_with_sites(ids, , info=None)

`"Name (website), Name2 (website2), ..."` for `ids` (name, not id).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.ocr(image, , backend=None, \*\*kwargs)

Read text from an image with any backend, returning a normalized result.

* **Parameters:**
  * **image** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes), PILImage, NDArray]) – A path, `http(s)` URL, `bytes`, PIL image, or numpy array.
  * **backend** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Backend id (see [`list_backends()`](#ocracy.list_backends)). Defaults to the first
    *installed* implemented backend (see [`get_default_backend()`](#ocracy.get_default_backend)).
  * **\*\*kwargs** – Normalized, backend-translated options (e.g. `languages`).
    Unknown options for the chosen backend are warned about and dropped.
* **Return type:**
  [`OcrResult`](ocracy.base.md#ocracy.base.OcrResult)
* **Returns:**
  An [`OcrResult`](ocracy.base.md#ocracy.base.OcrResult) (`str(result)` is the text).

### ocracy.read_text(image, , backend=None, \*\*kwargs)

Like [`ocr()`](#ocracy.ocr) but returns just the recognized text string.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.register_backend(backend_id, config, adapter=None)

Register a backend at runtime (for third-party plugins).

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Unique identifier.
  * **config** ([`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)) – `BACKEND_CONFIG`-shaped dict (needs at least `name`).
  * **adapter** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Optional pre-instantiated adapter; else loaded lazily from
    `config['module_path']` when first used.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### ocracy.requirements(backend_id, , gpu=False)

Return structured install [`Requirements`](#ocracy.Requirements) for `backend_id`.

Works for both implemented backends (uses the `ocracy[extra]` install and
the recipe) and ledger-only backends (falls back to the ledger’s
`python_install` string). Pass `gpu=True` to surface GPU wheel guidance.

* **Return type:**
  [`Requirements`](#ocracy.Requirements)

### ocracy.scaffold_backend(backend_id, , dest=None, overwrite=False, ledger=None, extra_overrides=None)

Create a new `ocracy/backends/<id>/` package from the template.

Pre-fills `config.py` from the backend’s ledger entry (if any) so you only
have to flesh out `param_map` and implement `adapter.py`’s `_read`.

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The ledger id (e.g. `"easyocr"`, `"google-vision"`). The
    on-disk module name uses underscores; the config `id` keeps the id
    verbatim.
  * **dest** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Target directory (defaults to `ocracy/backends/<id_underscored>`).
  * **overwrite** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Allow writing into an existing non-empty directory.
  * **ledger** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – A [`Catalog`](#ocracy.Catalog) to read the record from
    (defaults to the shipped catalog).
  * **extra_overrides** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – Extra config-key overrides applied on top of the record.
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  The path to the created backend package.

### ocracy.services *= <ServiceCollection backends=['aws-textract', 'azure-document-intelligence', 'claude-vision', 'easyocr', 'google-vision', 'gpt-4o-vision', 'mathpix', 'mistral-ocr', 'ocr-space', 'ocrmac', 'paddleocr', 'pix2tex-latex-ocr', 'rapidocr', 'tesseract', 'trocr-handwritten']>*

Singleton service collection for per-backend access (`services.tesseract`).

### ocracy.status_table(ids=None, , info=None, columns=None, run_tests=False, test_image=None)

Render an aligned Markdown table of backend status (also plain-text readable).

Rows are ordered tested → set-up → implemented → listed, then by name, so the
“live” backends float to the top. Pass a precomputed `info` to avoid re-running
tests; otherwise `run_tests` controls which set-up backends get OCR-tested.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.validate_adapter(backend_id, , image=None, expect_text=None)

Smoke-test a backend adapter end to end, returning a report dict.

Loads the adapter (reporting unavailability instead of raising), runs
`read` on a generated (or supplied) image, and checks the contract: an
[`OcrResult`](ocracy.base.md#ocracy.base.OcrResult) came back with text and/or blocks. Never
raises on a *recognition* mismatch — it returns what happened so callers can
decide.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Modules

| [`backends`](ocracy.backends.md#module-ocracy.backends)         | Implemented OCR backends.                                                                                        |
|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| [`base`](ocracy.base.md#module-ocracy.base)                 | Core types and normalized result objects for ocracy.                                                             |
| [`catalog`](ocracy.catalog.md#ocracy.catalog)                  | A filterable, dict-like collection of [`BackendInfo`](#ocracy.BackendInfo), keyed by id. |
| [`credentials`](ocracy.credentials.md#module-ocracy.credentials)   | Credential resolution for remote OCR backends.                                                                   |
| [`make_backend`](ocracy.make_backend.md#module-ocracy.make_backend) | Abstraction tools for *building* OCR facades.                                                                    |
| [`registry`](ocracy.registry.md#module-ocracy.registry)         | Backend discovery, registration, and lazy loading.                                                               |
| [`status`](ocracy.status.md#module-ocracy.status)             | Backend readiness status — four nested levels, info dicts, and a Markdown table.                                 |
| [`tools`](ocracy.tools.md#module-ocracy.tools)               | Command-line tools for ocracy (dispatched via `cw` in `__main__`).                                               |
| [`translation`](ocracy.translation.md#module-ocracy.translation)   | Parameter translation between ocracy's normalized kwargs and native engines.                                     |
| [`util`](ocracy.util.md#module-ocracy.util)                 | Image-input normalization and small shared helpers.                                                              |
