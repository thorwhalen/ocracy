# ocracy.translation

Parameter translation between ocracy’s normalized kwargs and native engines.

Every backend exposes its own parameter names and scales (`lang` vs
`languages` vs `language_hints`; thresholds in `0..1` vs `0..100`; pixel
vs point units). A backend declares a `param_map` in its `BACKEND_CONFIG`
mapping *normalized* names to native ones, and [`make_kwargs_translator()`](#ocracy.translation.make_kwargs_translator)
turns that declaration into a function that rewrites caller kwargs into the
shape the engine wants. This keeps the facade’s vocabulary stable while letting
each adapter stay a thin shim.

This mirrors the translation layer used by the sibling `denote` facade so the
two packages feel the same to read and extend.

### Functions

| [`make_kwargs_translator`](#ocracy.translation.make_kwargs_translator)(param_map, \*[, ...])   | Create a function that translates normalized kwargs to native kwargs.   |
|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [`validate_param`](#ocracy.translation.validate_param)(name, value, config)            | Validate a single parameter against `min`/`max`/`choices` in config.    |

### ocracy.translation.make_kwargs_translator(param_map, , on_unsupported='warn')

Create a function that translates normalized kwargs to native kwargs.

* **Parameters:**
  * **param_map** ([`Dict`](https://docs.python.org/3/library/typing.html#typing.Dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]]) – 

    Mapping of `normalized_name -> native config dict` where the
    config dict may have:
    - `native_name` (str): the backend’s parameter name (defaults to
      the normalized name).
    - `coerce` (callable): transform the value (e.g. seconds -> ms,
      `["en","fr"] -> "eng+fra"`).
    - `default` (Any): value to inject when the caller omits the param.
    - `None` as the whole value: the parameter is explicitly *not*
      supported by this backend.
  * **on_unsupported** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – What to do with caller params absent from `param_map`:
    `"warn"` (default), `"raise"`, or `"ignore"`.
* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]
* **Returns:**
  A `translate(**kwargs) -> dict` function.

### ocracy.translation.validate_param(name, value, config)

Validate a single parameter against `min`/`max`/`choices` in config.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
