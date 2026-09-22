# ocracy.registry

Backend discovery, registration, and lazy loading.

An *implemented* backend is a subpackage of [`ocracy.backends`](ocracy.backends.md#module-ocracy.backends) that ships
two things:

- `config.py` defining a `BACKEND_CONFIG` dict (id, pip_install, capabilities,
  `param_map`, …), and
- `adapter.py` defining an `Adapter` class whose `read(image, **kwargs)`
  returns an [`ocracy.base.OcrResult`](ocracy.base.md#ocracy.base.OcrResult).

This registry scans for those at first use, loads each adapter *lazily* (so
importing ocracy never imports heavy engine SDKs), and raises a friendly
`pip install` error if a backend’s dependency is missing. Third parties can
register their own backends at runtime via [`register_backend()`](#ocracy.registry.register_backend).

The design mirrors the sibling `denote` facade, adapted for OCR: the primary
capability is `"read"` (image -> text+layout), with optional extra capabilities
(`"tables"`, `"math"`, …) declared per backend.

### Module Attributes

| [`PRIMARY_CAPABILITY`](#ocracy.registry.PRIMARY_CAPABILITY)   | The capability every general OCR backend provides.   |
|-----------------------------------------------------------------------|------------------------------------------------------|

### Functions

| [`clear_registry`](#ocracy.registry.clear_registry)()                                | Clear all registered backends (useful for tests).                      |
|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`get_backend`](#ocracy.registry.get_backend)(backend_id)                         | Config + lazily-loaded adapter for a backend (raises on missing deps). |
| [`get_config`](#ocracy.registry.get_config)(backend_id)                          | A backend's `BACKEND_CONFIG` without loading its adapter.              |
| [`get_default_backend`](#ocracy.registry.get_default_backend)([capability, ...])          | Pick a sensible default backend id for a capability.                   |
| [`list_backends`](#ocracy.registry.list_backends)([capability])                     | Sorted ids of implemented backends, optionally filtered by capability. |
| [`register_backend`](#ocracy.registry.register_backend)(backend_id, config[, adapter]) | Register a backend at runtime (for third-party plugins).               |

### ocracy.registry.PRIMARY_CAPABILITY *= 'read'*

The capability every general OCR backend provides.

### ocracy.registry.clear_registry()

Clear all registered backends (useful for tests).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### ocracy.registry.get_backend(backend_id)

Config + lazily-loaded adapter for a backend (raises on missing deps).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.registry.get_config(backend_id)

A backend’s `BACKEND_CONFIG` without loading its adapter.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.registry.get_default_backend(capability='read', , require_available=True)

Pick a sensible default backend id for a capability.

Strategy (OCR-tuned): prefer a backend explicitly flagged `default_for` the
capability *and* whose dependency is importable; then any importable backend
for the capability; then — if `require_available` is False or nothing is
installed — the first registered candidate (using it will raise a helpful
install error).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.registry.list_backends(capability=None)

Sorted ids of implemented backends, optionally filtered by capability.

A backend matches `capability` if it appears in the backend’s
`capabilities` list (the primary `"read"` is implied for all).

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### ocracy.registry.register_backend(backend_id, config, adapter=None)

Register a backend at runtime (for third-party plugins).

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Unique identifier.
  * **config** ([`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)) – `BACKEND_CONFIG`-shaped dict (needs at least `name`).
  * **adapter** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Optional pre-instantiated adapter; else loaded lazily from
    `config['module_path']` when first used.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)
