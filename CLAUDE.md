# ocracy — agent & contributor guide

`ocracy` is one façade over many OCR engines — `ocracy.ocr(image) -> OcrResult`, the same shape whichever engine ran — plus a **ledger**: a researched, filterable catalog of 64 engines/services, of which **15 have a working façade today**. The ledger is data (`ocracy/data/backends.json`), not code; `implemented` is computed live from the registry, so it cannot lie about what runs.

It is **AI-first**: four skills ship inside the package (`ocracy/data/skills/`, bridged to `.claude/skills/` by relative symlinks), so an agent that `pip install ocracy`-ed gets the operating manual with the code.

## Start here

- [`ocracy`](ocracy/data/skills/ocracy/SKILL.md) — *using* it: the one-liner, reading the result, languages, credentials, the CLI. Read this first if you are driving ocracy.
- [`ocracy-choose-backend`](ocracy/data/skills/ocracy-choose-backend/SKILL.md) — filtering and comparing the 64-record ledger before committing to an engine.
- [`ocracy-install-backend`](ocracy/data/skills/ocracy-install-backend/SKILL.md) — getting one to actually run: system binaries, GPU wheels, first-run weights, API keys.
- [`ocracy-add-backend`](ocracy/data/skills/ocracy-add-backend/SKILL.md) — *building*: scaffold from the ledger → fill the adapter → validate. `ocracy/backends/tesseract/` is the worked example.

Background: [`ocracy/data/SCHEMA.md`](ocracy/data/SCHEMA.md) documents every ledger field; [`misc/docs/ocr_landscape_research.md`](misc/docs/ocr_landscape_research.md) is the cited research the ledger was distilled from.

## The granularity fact — read this before you touch `result.words`

**Every implemented backend emits exactly ONE granularity level.** There is no promotion, no synthesis, no grouping: an adapter builds blocks at whatever level its engine natively reports and nothing merges words into lines or splits lines into words afterwards. `OcrResult.words` and `OcrResult.lines` are both `at_level(...)` filters over the same flat `blocks` list, so **the level you did not ask for is an empty list — and an empty list is not an error.** A caller that needs word boxes and picks a line-level backend gets `[]`, no exception, no warning, and a silently empty downstream pipeline.

| Backend | `blocks` level | `.words` | `.lines` |
|---|---|---|---|
| `tesseract` | `word` | populated | **empty** |
| `google-vision` | `word` | populated | **empty** |
| `aws-textract` | `word` | populated | **empty** |
| `azure-document-intelligence` | `word` | populated | **empty** |
| `ocr-space` | `word` | populated | **empty** |
| `easyocr` | `line` | **empty** | populated |
| `rapidocr` | `line` | **empty** | populated |
| `paddleocr` | `line` | **empty** | populated |
| `ocrmac` | `line` | **empty** | populated |
| `claude-vision` | *(none)* | **empty** | **empty** |
| `gpt-4o-vision` | *(none)* | **empty** | **empty** |
| `mathpix` | *(none)* | **empty** | **empty** |
| `mistral-ocr` | *(none)* | **empty** | **empty** |
| `pix2tex-latex-ocr` | *(none)* | **empty** | **empty** |
| `trocr-handwritten` | *(none)* | **empty** | **empty** |

The six *(none)* rows return `OcrResult.from_text(...)`: `blocks == []` entirely, so `result.text` / `result.markdown` is the whole payload and `mean_confidence` is `None`.

Three consequences, each of them visible in the repo right now — two are places the package's own documentation says something the code does not do:

1. **The ledger's `bounding_boxes` flag describes the ENGINE, not ocracy's adapter, and it over-reports.** `claude-vision`, `mathpix` and `mistral-ocr` are all `bounding_boxes: true` in `backends.json` — each vendor's API can return geometry — yet all three adapters end in `OcrResult.from_text()` and return `blocks == []`. So `ocracy.find(bounding_boxes=True)` is a *shopping list of engines worth wrapping properly*, never a promise about what `ocracy.ocr()` will hand back today. (`gpt-4o-vision`, `pix2tex-latex-ocr` and `trocr-handwritten` are honestly `false`.)
2. **Iterating a result does not give you lines.** `OcrResult.__iter__` yields *all* blocks at whatever level they are, and `base.py`'s docstring calls them "lines by default" — true for the four line-level backends, wrong for the five word-level ones, and an empty loop for the other six. Iterate for "whatever units this engine gave me"; call `.lines` / `.words` only when you know the backend, or check both.
3. **`ocracy.LEVELS` is not the granularity levels.** `__init__.py` imports `LEVELS` from `ocracy.base` and then again from `ocracy.status`, and the second import wins: `ocracy.LEVELS == ("all", "implemented", "set_up", "tested")` — the readiness ladder. The granularity tuple `("page", "block", "paragraph", "line", "word", "char")` is only reachable as `ocracy.base.LEVELS`. `__all__` lists `"LEVELS"` twice, which is the tell.

If your code needs a specific granularity, **assert it** rather than trusting a backend id:

```python
result = ocracy.ocr(img, backend=chosen)
if not result.words:
    raise ValueError(f"{chosen} does not report word-level boxes")
```

## Capability map

| Want | Reach for |
|---|---|
| Just the text | `ocracy.read_text(image)` → `str` |
| Text + geometry + confidence | `ocracy.ocr(image)` → `OcrResult` |
| A specific engine, normalized options | `ocracy.ocr(image, backend="easyocr", languages=["en", "fr"])` |
| A specific engine, its own options | `ocracy.services.tesseract.read(img, psm=6)` |
| The raw engine object | `ocracy.services.tesseract.adapter` |
| Which engines run *here, now* | `ocracy.available_backends()` / `ocracy.doctor()` |
| Which engines ocracy can run at all | `ocracy.list_backends()` (15) |
| Every engine researched | `ocracy.catalog` (64) |
| Pick an engine on the merits | `ocracy.find(is_local=True, open_source=True)`, `.can("math")`, `.supports_language("Arabic")` |
| The exact install plan for this OS | `ocracy.requirements("paddleocr").instructions()` |
| Run that plan | `ocracy.install("rapidocr", yes=True)` |
| Readiness of everything, four levels | `ocracy.status_table()` |
| Wrap a 16th engine | `scaffold_backend(id)` → adapter → `validate_adapter(id)` |

Every name above is a top-level `ocracy` export (`scaffold_backend` / `validate_adapter` also live in `ocracy.make_backend`, which is where new façade-building machinery goes). The CLI mirrors it (`ocracy read|backends|find|info|status|doctor|requirements|install|scaffold|validate`), built by `cw` from the signatures in `ocracy/tools.py` — so a new CLI command is a new function in `_dispatch_funcs`, never an argparse edit.

## Architecture

```
Facade          ocracy.ocr / read_text / find            (ocracy/__init__.py)
Services        services.<id>.read / .adapter            (services.py — three tiers)
Registry        lazy discovery of ocracy/backends/*      (registry.py)
Translation     normalized kwargs -> native kwargs       (translation.py, from config's param_map)
Adapters        one subpackage per engine                (backends/<id>/{config,adapter}.py)
Normalization   OcrResult / TextBlock / BBox             (base.py)

Ledger          64 records, data not code                (data/backends.json, read by catalog.py)
Readiness       all ⊇ implemented ⊇ set_up ⊇ tested      (status.py, install.py, credentials.py)
```

A backend is discovered structurally — a subpackage of `ocracy.backends` with a `BACKEND_CONFIG` in `config.py` and an `Adapter` in `adapter.py`. There is no registration list to edit; a leading `_` (as in `_template`) excludes a directory. Third parties can add one at runtime with `register_backend`.

## Invariants that are easy to violate

1. **`import ocracy` is dependency-free.** `dependencies = []` in `pyproject.toml` is deliberate; every engine SDK, Pillow, numpy and pandas are extras, imported **inside** the function that needs them. A module-level `import requests` in an adapter breaks the whole package for everyone who did not install that backend.
2. **The registry probes without loading.** `_is_available` imports only `config["import_name"]`; adapters are instantiated lazily by `_load_adapter`. Keep availability checks off the adapter, or `ocracy.doctor()` starts downloading model weights.
3. **A missing dependency and a missing credential are different errors, and both must name the fix.** `registry._load_adapter` turns an `ImportError` into a `pip install` line plus `ocracy.requirements(...)`; `credentials.resolve_credential` names the env var *and* links where to get a key. Never let either surface as a bare traceback.
4. **Confidence is normalized to `[0, 1]` at the adapter boundary**, via `make_block(..., conf_scale=...)` (Tesseract's `0..100` is the canonical case). A raw engine scale reaching `TextBlock.confidence` corrupts `mean_confidence` and `filter_confidence` for every caller.
5. **Boxes are pixels, top-left origin.** Engines that report normalized or bottom-left coordinates convert in the adapter — `ocrmac` is the worked example (Vision gives normalized bottom-left `(x, y, w, h)`).
6. **The ledger is the SSOT for engine facts and never learns them from code**; `implemented` is the one computed field. If you make a claim about an engine, it belongs in `backends.json` with a citation, not in a docstring.
7. **`filter_confidence` drops blocks whose confidence is `None`.** On the six text-only backends that means it empties the result. Documented in `base.py`, still surprising.
8. **Adding a backend means adding its extra**, its `_RECIPES` entry in `install.py` when the install is non-trivial, its credential guidance in `credentials.py` when remote, and a row in the granularity table above.

## Known gaps and consolidation opportunities

- **`dn` reads text out of scanned PDFs with its own Tesseract integration, bypassing ocracy entirely.** `$PP/t/dn/dn/ocr.py` (306 lines, zero references to ocracy anywhere in the repo) shells to `pytesseract` directly and carries its own copy of exactly what ocracy exists to own: a `find_tesseract()` binary search with a hardcoded candidate-path list, an `_importable()` probe, a `check_ocr_requirements()` / `ocr_is_available()` readiness pair, and an `_INSTALL_HINTS` table of per-OS install commands. Those are `ocracy.install.requirements()` / `check()` / `doctor()` and the `_RECIPES["tesseract"]` entry, re-derived. The consolidation is `dn` calling `ocracy.ocr(page_image, backend=...)`, which would also make `dn`'s OCR engine-swappable (its docstring's "the fix is ... run it through Tesseract" is currently a hard-coded choice) at the cost of one dependency in `dn[ocr]`. **Not done, and not ocracy's call to make** — `dn` is a separate package with its own release cycle; raise it there.
- **Nothing in the code declares what an adapter emits, so the granularity table above lives in prose — in three places (here, the README, the `ocracy` skill).** That is exactly the shape that drifts, and it is discoverable today only by reading fifteen `adapter.py` files for their `level=` argument. The fix is a **declared field on `BACKEND_CONFIG`** — say `"emits_levels": ["word"]` — *not* a ledger field: the ledger describes 64 engines' *capabilities*, and putting granularity there would repeat the exact category error that makes `bounding_boxes` over-report. Declared per adapter it is (a) mechanically testable — `tests/test_backends.py` already runs `validate_adapter` per backend, so one assertion that the emitted blocks' levels match the declaration makes the docs self-enforcing; (b) surfaceable through `ServiceHandle.info`; and (c) free to filter on, because `Catalog._load` already merges a computed per-record field (`implemented`) from the registry, and `Catalog.filter(**criteria)` is open over record fields — so `ocracy.find(implemented=True, emits_levels="word")` would work with no filter change, provided `emits_levels` joins `catalog._TEXT_MEMBERSHIP_FIELDS` so a list-valued field gets membership rather than equality semantics. **Not implemented.**
- **`ocracy` reads images, not PDFs.** Callers rasterize pages first. This is why `dn` grew its own path.
- **Only `tesseract` is `default_for` "read"**, so `get_default_backend()` falls through to the first *available* candidate alphabetically when pytesseract is absent — which on a machine with only `requests` installed is `mathpix`, a paid remote backend. `tests/test_registry_services.py::test_default_backend_resolves` asserts `tesseract` and therefore only passes where pytesseract is importable.

## Tests

`python -m pytest -q` from the repo root — that is also where the current count comes from, so don't pin one here. Three things to know:

- **The suite is offline and free.** Structural tests (config integrity, param translation, catalog filtering, status levels) run with no engine installed; end-to-end adapter checks skip themselves when a dependency is missing, and no test ever makes a billed API call. `run_tests=True` on `backend_info` / `status_table` (`ocracy status --run-tests`) **does** make real calls for set-up remotes — it is a diagnostic verb, never a test.
- **No docstring under `ocracy/` is ever executed, even though CI asks for it.** wads' `run-tests-uv` action appends `--doctest-modules`, but it passes no path, so pytest falls back to `testpaths = ["tests"]` and never descends into the package — measured: CI's exact invocation collects 83 items, all from `tests/`. Today nothing is lost (the package's docstrings use `::` literal blocks, and there is not one `>>>` in `ocracy/*.py`), but the day someone writes a doctest here believing it is a test, it will be silently uncollected. This is the `an#61` trap; the fix is adding `"ocracy"` to `testpaths`.
- **`doctest_optionflags` in `pyproject.toml` lists `NORMALIZE_WHITESPACE`; CI overrides the whole key with `-o doctest_optionflags='ELLIPSIS IGNORE_EXCEPTION_DETAIL'`.** So if doctests are ever enabled, any example relying on whitespace normalization passes locally and fails in CI. Make the ini key match what CI passes, in the same commit.

## Conventions

- Favour functional style; `dataclasses` for data (`OcrResult`, `TextBlock`, `BBox`, `Requirements`); small focused helpers, `_underscore` when module-private.
- Arguments beyond the third position are keyword-only; most public functions here are keyword-only from the second.
- No magic numbers outside a named module constant. Per-engine knowledge belongs in `BACKEND_CONFIG` or `install._RECIPES`, never inline in an adapter.
- Every module needs a top-level docstring — `D100` is the *only* rule `[tool.ruff.lint].select` turns on, so it is the one lint that can fail CI here, and the docstrings are auto-extracted for the published docs.
- `ocracy/__init__.py` only re-exports and defines the three facade functions — no engine knowledge.
- `__version__` comes from installed distribution metadata; `pyproject.toml` is the SSOT and the wads release job bumps it. Never hardcode it.
- **CI: a push to the default branch publishes to PyPI and bumps the version.** Don't re-run a default-branch workflow casually.

The architecture deliberately mirrors the sibling façade packages [`denote`](https://github.com/thorwhalen/denote) (audio → symbol), [`aix`](https://github.com/thorwhalen/aix) (LLM providers) and [`arioso`](https://github.com/thorwhalen/arioso) (music generation): ledger + registry + adapters + three tiers of access. A change to that shape should be made in all of them or in none.
