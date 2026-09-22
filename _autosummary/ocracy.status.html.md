# ocracy.status

Backend readiness status — four nested levels, info dicts, and a Markdown table.

ocracy describes far more OCR engines than any one machine has ready to run, so it
helps to know, at a glance, where each one stands. Four **nested** levels:

1. **all** — every engine in the ledger (`ocracy/data/backends.json`).
2. **implemented** — ocracy ships a working facade for it (`⊆ all`).
3. **set_up** — ready to run *here, now*: the engine/client library is importable
   and, for a remote backend, its credential env var is present (`⊆ implemented`).
4. **tested** — actually produced text from a small image on this machine (`⊆ set_up`).

`all ⊇ implemented ⊇ set_up ⊇ tested`.

API:

- [`backend_ids()`](#ocracy.status.backend_ids) — the id list at a level.
- [`backend_info()`](#ocracy.status.backend_info) — `{id: {...all ledger fields..., implemented, set_up, tested}}`.
- [`status_table()`](#ocracy.status.status_table) — an aligned Markdown table (also readable as plain text).
- [`names_with_sites()`](#ocracy.status.names_with_sites) — `"Name (website), ..."` for a set of ids.

#### NOTE
computing **tested** runs real OCR — for *remote* backends that means a real
(possibly billed) API call. Use the `run_tests` argument to control exactly which
backends get called.

### Functions

| [`is_set_up`](#ocracy.status.is_set_up)(backend_id)                      | Ready to run here & now.                                                       |
|---------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`is_tested`](#ocracy.status.is_tested)(backend_id, \*[, image])         | Actually run OCR on `image` (a generated one if None); True iff it worked.     |
| [`backend_ids`](#ocracy.status.backend_ids)([level, info, test_image])     | Sorted backend ids at a readiness `level` (one of `LEVELS`).                   |
| [`backend_info`](#ocracy.status.backend_info)([ids, run_tests, test_image]) | Per-backend status: every ledger field plus `implemented`/`set_up`/`tested`.   |
| [`status_table`](#ocracy.status.status_table)([ids, info, columns, ...])    | Render an aligned Markdown table of backend status (also plain-text readable). |
| [`names_with_sites`](#ocracy.status.names_with_sites)(ids, \*[, info])          | `"Name (website), Name2 (website2), ..."` for `ids` (name, not id).            |

### ocracy.status.backend_ids(level='all', , info=None, test_image=None)

Sorted backend ids at a readiness `level` (one of `LEVELS`).

Pass a precomputed `info` (from [`backend_info()`](#ocracy.status.backend_info)) to avoid recomputation
— important for `"tested"`, which otherwise re-runs OCR.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ocracy.status.backend_info(ids=None, , run_tests=False, test_image=None)

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

### ocracy.status.is_set_up(backend_id)

Ready to run here & now.

Requires the engine/client to be importable (local *and* remote), and — for a
remote backend — its (primary) credential env var to resolve. So a remote
whose key is set but whose client library isn’t installed is *not* set up
(it couldn’t actually run). Returns False for ledger-only backends.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.status.is_tested(backend_id, , image=None)

Actually run OCR on `image` (a generated one if None); True iff it worked.

For remote backends this performs a real API call. Returns False if the
backend isn’t set up or the run fails.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.status.names_with_sites(ids, , info=None)

`"Name (website), Name2 (website2), ..."` for `ids` (name, not id).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.status.status_table(ids=None, , info=None, columns=None, run_tests=False, test_image=None)

Render an aligned Markdown table of backend status (also plain-text readable).

Rows are ordered tested → set-up → implemented → listed, then by name, so the
“live” backends float to the top. Pass a precomputed `info` to avoid re-running
tests; otherwise `run_tests` controls which set-up backends get OCR-tested.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
