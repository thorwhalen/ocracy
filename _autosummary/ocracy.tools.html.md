# ocracy.tools

Command-line tools for ocracy (dispatched via `cw` in `__main__`).

Each function here is a thin, CLI-friendly wrapper over the Python API; `cw`
turns their signatures into subcommands and options. Run `ocracy <command>
--help` (after `pip install 'ocracy[cli]'`) or `python -m ocracy <command>`.

### Functions

| [`read`](#ocracy.tools.read)(image, \*[, backend, languages, output])     | OCR an image and print the result.                                                  |
|----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| [`backends`](#ocracy.tools.backends)(\*[, capability])                        | List the backends ocracy can run right now (optionally by capability).              |
| [`info`](#ocracy.tools.info)(backend_id)                                  | Print a backend's full ledger record as JSON.                                       |
| [`find`](#ocracy.tools.find)(\*[, local, remote, free, implemented, ...]) | Filter the ledger and print matching backends (id, where, pricing, best-for).       |
| [`scaffold`](#ocracy.tools.scaffold)(backend_id, \*[, dest])                  | Generate a new backend package from its ledger entry.                               |
| [`validate`](#ocracy.tools.validate)(backend_id)                              | Smoke-test a backend adapter end to end and print the report.                       |
| [`requirements`](#ocracy.tools.requirements)(backend_id, \*[, gpu])               | Show what a backend needs to run (pip, system deps, GPU, weights, creds).           |
| [`doctor`](#ocracy.tools.doctor)()                                          | Report which backends are usable now, and how to install the rest.                  |
| [`install`](#ocracy.tools.install)(backend_id, \*[, gpu, yes])               | Plan (default) or run (`--yes`) the pip install for a backend.                      |
| [`status`](#ocracy.tools.status)(\*[, level, run_tests, names])             | Print an OCR-backend readiness table (levels: all ⊇ implemented ⊇ set_up ⊇ tested). |

### ocracy.tools.backends(, capability=None)

List the backends ocracy can run right now (optionally by capability).

* **Parameters:**
  **capability** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Filter to a capability, e.g. `math`, `tables`, `handwriting`.

### ocracy.tools.doctor()

Report which backends are usable now, and how to install the rest.

### ocracy.tools.find(, local=False, remote=False, free=False, implemented=False, handwriting=False, math=False, tables=False, language=None)

Filter the ledger and print matching backends (id, where, pricing, best-for).

Flags compose (AND). Example: `ocracy find --local --free --handwriting`.

* **Parameters:**
  * **local** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only backends that run locally.
  * **remote** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only hosted/remote backends.
  * **free** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only free / open-source backends.
  * **implemented** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only backends ocracy can run today.
  * **handwriting** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only backends that read handwriting.
  * **math** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only backends that read math/formulas.
  * **tables** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Keep only backends that extract tables.
  * **language** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Keep only backends whose languages mention this name/code.

### ocracy.tools.info(backend_id)

Print a backend’s full ledger record as JSON.

* **Parameters:**
  **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – A ledger id, e.g. `google-vision` (see `ocracy find`).

### ocracy.tools.install(backend_id, , gpu=False, yes=False)

Plan (default) or run (`--yes`) the pip install for a backend.

Without `--yes` it prints the plan and changes nothing. System deps and GPU
wheels are surfaced, not run automatically.

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Backend id to install, e.g. `rapidocr`.
  * **gpu** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Surface GPU-wheel guidance.
  * **yes** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Actually run `pip install` (otherwise just print the plan).

### ocracy.tools.read(image, , backend=None, languages=None, output='text')

OCR an image and print the result.

* **Parameters:**
  * **image** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path or http(s) URL to the image.
  * **backend** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Backend id (default: first installed). See `ocracy backends`.
  * **languages** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Comma-separated language codes, e.g. `en,fr`.
  * **output** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – `text` (default), `json` (text + blocks), or `markdown`.

### ocracy.tools.requirements(backend_id, , gpu=False)

Show what a backend needs to run (pip, system deps, GPU, weights, creds).

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Backend id, e.g. `paddleocr`.
  * **gpu** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Include GPU-wheel guidance.

### ocracy.tools.scaffold(backend_id, , dest=None)

Generate a new backend package from its ledger entry.

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The ledger id to scaffold (e.g. `surya`).
  * **dest** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional destination directory.

### ocracy.tools.status(, level='all', run_tests=False, names=False)

Print an OCR-backend readiness table (levels: all ⊇ implemented ⊇ set_up ⊇ tested).

* **Parameters:**
  * **level** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Restrict rows to a level: `all` | `implemented` | `set_up` | `tested`.
  * **run_tests** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Actually OCR-test the set-up backends — makes real API calls for
    set-up remotes (off by default, so a plain `ocracy status` never bills you).
  * **names** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Also print, per level, a comma-separated `Name (website)` list.

### ocracy.tools.validate(backend_id)

Smoke-test a backend adapter end to end and print the report.

* **Parameters:**
  **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend id to validate (e.g. `tesseract`).
