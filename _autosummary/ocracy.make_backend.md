# ocracy.make_backend

Abstraction tools for *building* OCR facades.

Writing a new backend should be mostly declarative. This module supplies the
reusable machinery so an adapter is just “call the engine, return normalized
blocks”:

- [`BaseOcrAdapter`](#ocracy.make_backend.BaseOcrAdapter) — subclass it and implement `_read()`;
  kwarg translation (via the backend’s `param_map`) is handled for you.
- [`make_block()`](#ocracy.make_backend.make_block) / [`as_bbox()`](#ocracy.make_backend.as_bbox) — build normalized [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock)
  / [`BBox`](ocracy.base.md#ocracy.base.BBox) from whatever shape the engine returned, including
  confidence-scale normalization (e.g. Tesseract’s `0..100` -> `0..1`).
- [`scaffold_backend()`](#ocracy.make_backend.scaffold_backend) — generate a new `ocracy/backends/<id>/` package from
  the template, pre-filled from the ledger entry. This is the one-command way to
  start a facade for any backend in the catalog.
- [`make_test_image()`](#ocracy.make_backend.make_test_image) / [`validate_adapter()`](#ocracy.make_backend.validate_adapter) — smoke-test an adapter end
  to end so you know a new facade actually works.

These are the “abstraction tools and skills that know the process” — the
companion `SKILL.md` walks an agent (or human) through using them.

### Functions

| [`make_block`](#ocracy.make_backend.make_block)(text, \*[, bbox, confidence, ...])   | Build a normalized [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock).     |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| [`as_bbox`](#ocracy.make_backend.as_bbox)(obj)                                    | Coerce common bbox shapes into a [`BBox`](ocracy.base.md#ocracy.base.BBox). |
| [`normalize_confidence`](#ocracy.make_backend.normalize_confidence)(value, \*[, scale])        | Normalize a raw confidence to `[0, 1]` (dividing by `scale`).                                            |
| [`scaffold_backend`](#ocracy.make_backend.scaffold_backend)(backend_id, \*[, dest, ...])   | Create a new `ocracy/backends/<id>/` package from the template.                                          |
| [`make_test_image`](#ocracy.make_backend.make_test_image)([text, size, font_size])        | Render a black-on-white test image with `text` (needs Pillow).                                           |
| [`validate_adapter`](#ocracy.make_backend.validate_adapter)(backend_id, \*[, image, ...])  | Smoke-test a backend adapter end to end, returning a report dict.                                        |

### Classes

| [`BaseOcrAdapter`](#ocracy.make_backend.BaseOcrAdapter)(config)   | Optional base class for backend adapters.   |
|---------------------------------------------------------------------------|---------------------------------------------|

### *class* ocracy.make_backend.BaseOcrAdapter(config)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Optional base class for backend adapters.

Stores the config, builds a kwarg translator from `config['param_map']`,
and implements `read` as: translate normalized kwargs -> native kwargs ->
`_read()`. Subclasses implement `_read()` and return an
[`OcrResult`](ocracy.base.md#ocracy.base.OcrResult).

Adapters are not *required* to subclass this — the registry only needs an
`Adapter` class with a `read(image, **kwargs)` method — but doing so
removes the boilerplate.

### ocracy.make_backend.as_bbox(obj)

Coerce common bbox shapes into a [`BBox`](ocracy.base.md#ocracy.base.BBox).

Accepts a `BBox` (returned as-is), a 4-tuple `(x0, y0, x1, y1)`, or a
polygon `[(x, y), ...]` (4+ points). `None` passes through.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`BBox`](ocracy.base.md#ocracy.base.BBox)]

### ocracy.make_backend.make_block(text, , bbox=None, confidence=None, conf_scale=1.0, level='word', language=None, \*\*meta)

Build a normalized [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock).

`bbox` may be any shape accepted by [`as_bbox()`](#ocracy.make_backend.as_bbox). `confidence` is
normalized to `[0, 1]` via `conf_scale` (e.g. `conf_scale=100` for
percent-scale engines).

* **Return type:**
  [`TextBlock`](ocracy.base.md#ocracy.base.TextBlock)

### ocracy.make_backend.make_test_image(text='OCR test 123', , size=(640, 140), font_size=48)

Render a black-on-white test image with `text` (needs Pillow).

Uses a real TrueType font (DejaVuSans, then Pillow’s sized default) at a
legible size so OCR engines can actually read it — important for
[`validate_adapter()`](#ocracy.make_backend.validate_adapter) to be a meaningful smoke test.

### ocracy.make_backend.normalize_confidence(value, , scale=1.0)

Normalize a raw confidence to `[0, 1]` (dividing by `scale`).

`None` passes through. Use `scale=100` for engines that report `0..100`.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

### ocracy.make_backend.scaffold_backend(backend_id, , dest=None, overwrite=False, ledger=None, extra_overrides=None)

Create a new `ocracy/backends/<id>/` package from the template.

Pre-fills `config.py` from the backend’s ledger entry (if any) so you only
have to flesh out `param_map` and implement `adapter.py`’s `_read`.

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The ledger id (e.g. `"easyocr"`, `"google-vision"`). The
    on-disk module name uses underscores; the config `id` keeps the id
    verbatim.
  * **dest** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Target directory (defaults to `ocracy/backends/<id_underscored>`).
  * **overwrite** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Allow writing into an existing non-empty directory.
  * **ledger** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – A [`Catalog`](ocracy.md#ocracy.Catalog) to read the record from
    (defaults to the shipped catalog).
  * **extra_overrides** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – Extra config-key overrides applied on top of the record.
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  The path to the created backend package.

### ocracy.make_backend.validate_adapter(backend_id, , image=None, expect_text=None)

Smoke-test a backend adapter end to end, returning a report dict.

Loads the adapter (reporting unavailability instead of raising), runs
`read` on a generated (or supplied) image, and checks the contract: an
[`OcrResult`](ocracy.base.md#ocracy.base.OcrResult) came back with text and/or blocks. Never
raises on a *recognition* mismatch — it returns what happened so callers can
decide.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
