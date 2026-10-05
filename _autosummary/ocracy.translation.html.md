# ocracy.translation

Parameter translation between ocracy’s normalized kwargs and native engines.

Every backend exposes its own parameter names and scales (`lang` vs
`languages` vs `language_hints`; thresholds in `0..1` vs `0..100`; pixel
vs point units). A backend declares a `param_map` in its `BACKEND_CONFIG`
mapping *normalized* names to native ones, and [`make_kwargs_translator()`](#ocracy.translation.make_kwargs_translator)
turns that declaration into a function that rewrites caller kwargs into the
shape the engine wants.

The machinery lives in the facade kit ([`ocracy.kit.translation`](ocracy.kit.translation.html.md#module-ocracy.kit.translation)), shared
with the fleet’s other facades; this module keeps ocracy’s original
`translate(**kwargs) -> dict` shape for existing callers. New code that wants
the drops and clamps as notes uses [`ocracy.kit.make_translator()`](ocracy.kit.html.md#ocracy.kit.make_translator) directly,
as [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter) does.

### Functions

| [`make_kwargs_translator`](#ocracy.translation.make_kwargs_translator)(param_map, \*[, ...])   | Create a function that translates normalized kwargs to native kwargs.   |
|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [`validate_param`](#ocracy.translation.validate_param)(name, value, config)            | Validate a single parameter against `min`/`max`/`choices` in config.    |

### ocracy.translation.make_kwargs_translator(param_map, , on_unsupported='warn')

Create a function that translates normalized kwargs to native kwargs.

* **Parameters:**
  * **param_map** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]]) – Mapping of `normalized_name -> spec`; see
    [`ocracy.kit.translation`](ocracy.kit.translation.html.md#module-ocracy.kit.translation) for every spec form (`None` means the
    backend does not support the parameter).
  * **on_unsupported** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – `"warn"` (default), `"raise"`, `"note"` or
    `"ignore"`. The notes are discarded by this dict-returning form.
* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]
* **Returns:**
  A `translate(**kwargs) -> dict` function.

### ocracy.translation.validate_param(name, value, config)

Validate a single parameter against `min`/`max`/`choices` in config.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
