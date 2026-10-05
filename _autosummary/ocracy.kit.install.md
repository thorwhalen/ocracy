# ocracy.kit.install

Install plans: what a backend needs on *this* OS, as data an agent can act on.

Many backends are not one `pip install` away: a system binary (`brew install
tesseract`), a GPU wheel, first-run model weights, a credential. A package keeps
that knowledge as a `recipes` table (backend id -> recipe) and this module turns
one recipe into a [`Requirements`](#ocracy.kit.install.Requirements) whose [`instructions()`](#ocracy.kit.install.Requirements.instructions) is a
copy-pasteable plan:

```default
>>> req = build_requirements(
...     "tess", package="ocracy", implemented=True, available=False,
...     recipe={"system": {"linux": ["apt-get install tesseract-ocr"]}},
...     platform="linux",
... )
>>> req.pip_command
'pip install "ocracy[tess]"'
>>> req.system
['apt-get install tesseract-ocr']
```

A recipe needs only the fields that differ from the trivial
`pip install "<package>[<id>]"`: `extra` (the pyproject extra, when it differs
from the id), `system` (platform -> shell commands), `system_note`, `gpu` (an
alternative pip line), `weights` (first-run downloads), `heavy`, `alt` (a
lighter backend) and `notes`.

[`run_install()`](#ocracy.kit.install.run_install) executes the pip part of a plan (`yes=True` only) and verifies
it in a fresh interpreter. System commands and GPU wheels are surfaced, never run:
they need sudo, brew, or a CUDA choice only the user can make.

The registry and ledger lookups stay in the package (they are the package’s
knowledge); [`ocracy.install`](ocracy.md#ocracy.install) is the worked example. Stdlib only; imports
nothing else from ocracy.

### Functions

| [`current_platform`](#ocracy.kit.install.current_platform)()                               | `'darwin'`, `'linux'`, `'windows'`, or `sys.platform` for anything else.                                              |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| [`build_requirements`](#ocracy.kit.install.build_requirements)(backend_id, \*, package, ...) | Build [`Requirements`](#ocracy.kit.install.Requirements) for `backend_id` from its recipe and known facts. |
| [`run_install`](#ocracy.kit.install.run_install)(req, \*, package[, yes, ...])        | Plan (default) or run (`yes=True`) the pip install that `req` describes.                                              |

### Classes

| [`Requirements`](#ocracy.kit.install.Requirements)(backend_id, implemented, ...[, ...])   | What a backend needs to run, structured for an agent to act on.   |
|------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|

### *class* ocracy.kit.install.Requirements(backend_id, implemented, available, is_local, is_remote, pip_command, extra=None, system=<factory>, system_note=None, gpu=None, weights=None, heavy=False, alternative=None, credentials=<factory>, notes=<factory>, verify_command=None, alternative_label='Lighter alternative')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What a backend needs to run, structured for an agent to act on.

#### instructions()

An agent- and human-readable, copy-pasteable install plan.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.kit.install.build_requirements(backend_id, , package, implemented, available, recipe=None, is_local=False, is_remote=False, ledger_pip='', credentials=(), platform=None, verify_command=None, unimplemented_note=None, alternative_label='Lighter alternative')

Build [`Requirements`](#ocracy.kit.install.Requirements) for `backend_id` from its recipe and known facts.

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend’s id.
  * **package** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The distribution whose extra installs it (`pip install "pkg[x]"`).
  * **implemented** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether the package ships a facade for it.
  * **available** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether it is usable right now (the package’s own probe).
  * **recipe** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)]) – Its row of the package’s recipes table (see the module docstring).
  * **is_remote** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – From the backend’s config or ledger record.
  * **ledger_pip** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The ledger’s install line, used for a backend not implemented.
  * **credentials** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – `export` lines (see [`credential_lines()`](ocracy.kit.credentials.md#ocracy.kit.credentials.credential_lines)).
  * **platform** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Override [`current_platform()`](#ocracy.kit.install.current_platform) (for tests and docs).
  * **verify_command** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – The shell line shown as `Verify:`.
  * **unimplemented_note** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Appended to `notes` when not implemented.
  * **alternative_label** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The wording before `alt` in the instructions.
* **Return type:**
  [`Requirements`](#ocracy.kit.install.Requirements)

### ocracy.kit.install.current_platform()

`'darwin'`, `'linux'`, `'windows'`, or `sys.platform` for anything else.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.kit.install.run_install(req, , package, yes=False, verify_code=None, upgrade=False)

Plan (default) or run (`yes=True`) the pip install that `req` describes.

* **Parameters:**
  * **req** ([`Requirements`](#ocracy.kit.install.Requirements)) – The plan, from [`build_requirements()`](#ocracy.kit.install.build_requirements).
  * **package** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The distribution whose extra to install.
  * **yes** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Actually run pip; otherwise a dry run that changes nothing.
  * **verify_code** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Python source run in a fresh interpreter after a successful
    install; `available_after` is whether it printed `True`.
  * **upgrade** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Pass `--upgrade` to pip.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  `{backend, requirements, ran, available_before, message?, pip_argv?,
  returncode?, stdout_tail?, stderr_tail?, available_after?, system_todo?}`.
