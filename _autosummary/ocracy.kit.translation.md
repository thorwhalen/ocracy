# ocracy.kit.translation

Canonical -> native keyword translation, with an honest unsupported-parameter policy.

A facade speaks one vocabulary (`languages`, `duration`, `seed`); each backend
speaks its own (`lang`, `audio_length_s`, `random_seed`). A backend declares a
`param_map` from canonical names to *specs*, and [`make_translator()`](#ocracy.kit.translation.make_translator) turns it
into a function that rewrites the caller’s canonical kwargs into native ones and
**reports every change** it made:

```default
>>> translate = make_translator(
...     {"languages": {"native_name": "lang", "coerce": "+".join},
...      "dpi": None},                       # known, explicitly unsupported
...     backend="tess", on_unsupported="note",
... )
>>> t = translate({"languages": ["eng", "fra"], "dpi": 300})
>>> t.kwargs
{'lang': 'eng+fra'}
>>> t.notes
['dpi=300 is not supported by tess; dropped']
>>> t.dropped
['dpi']
```

A spec is one of:

- `None` – the backend explicitly does not support the parameter;
- a `str` – a plain rename to that native name;
- a callable – coerce the value, keep the canonical name;
- a mapping with any of: `native_name` (`name` is accepted as an alias),
  `coerce`, `default` (injected when the caller omits the parameter),
  `choices` / `min` / `max` (checked on the *canonical* value), and
  `out_of_range` – `'raise'`, `'clamp'` (`min`/`max` only, with a note) or
  `'drop'` (handled like an unsupported parameter); the translator’s
  `out_of_range=` is the default – plus `unit` (shown in the clamp note).
  `native_name: None` means unsupported, exactly like a bare `None`.
  `adapter_handled: True` passes the value through under its canonical name, for
  the adapter to handle (whatever `native_name` says). Other keys
  (`description`…) are ignored.

The policy for a parameter the backend cannot honour is one of [`POLICIES`](#ocracy.kit.translation.POLICIES):
`'raise'` ([`UnsupportedParameter`](#ocracy.kit.translation.UnsupportedParameter)), `'warn'` (drop, note it, and
[`warnings.warn()`](https://docs.python.org/3/library/warnings.html#warnings.warn)), `'note'` (drop and note it), or `'ignore'` (an alias of
`'note'`: kept for the copies that used it, and still never silent – the drop is
always in [`Translation.notes`](#ocracy.kit.translation.Translation.notes) and [`Translation.dropped`](#ocracy.kit.translation.Translation.dropped)).

Notes, warnings and errors show the dropped value, shortened, so a reader knows what
was lost – but never a secret, because notes end up in results that get stored and
logged. A parameter or mapping key named like one ([`is_secret_name()`](#ocracy.kit.translation.is_secret_name):
`api_key`, `x-api-key`, `accessToken`, `client_secret`…) or a string shaped
like one (`Bearer ...`, `https://user:pw@host`, `?key=...`) is shown as
`<redacted>`, and anything that is not plain data (an object, bytes) is shown only
as its type. This is best-effort by name and shape: a secret passed under an
innocent name, with no recognisable shape, can still show – so credentials belong
in parameters named for them.

Several choices are declared once, when the translator is made, and each was a real
divergence between the fleet’s copies (see `docs/adr/0001-facade-kit.md`):

- `always_raise` – parameters that *carry meaning* (`lyrics`, `seed`,
  `negative_prompt`): dropping them changes what the caller gets, so they raise
  under the backend’s policy. A caller who passes `on_unsupported=` to the
  translator call has chosen explicitly, and that choice wins.
- `vocabulary` – the facade’s canonical names mapped to their defaults. With it,
  an unsupported parameter left at its default (or `None`) was never asked for, so
  it is skipped rather than reported as dropped, and an unknown name is worded
  “not a parameter of” rather than “not supported by”.
- `skip_none` / `passthrough` – a `None` value means “unset” and is never sent;
  named adapter-only parameters (credentials, clients) go through untranslated.
- `stacklevel` – which frame a `'warn'` points at, counted from the code that
  calls the translator (1 = that code, 2 = its caller…).

Stdlib only; imports nothing else from ocracy.

### Module Attributes

| [`POLICIES`](#ocracy.kit.translation.POLICIES)        | How a parameter the backend cannot honour is handled.                                                                                                                                                      |
|------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`OUT_OF_RANGE`](#ocracy.kit.translation.OUT_OF_RANGE)    | How a value outside a spec's `choices` / `min` / `max` is handled.                                                                                                                                         |
| [`SECRET_SEGMENTS`](#ocracy.kit.translation.SECRET_SEGMENTS) | Name segments (split on `_ - .`, spaces and camelCase, case-insensitive) that make a value secret wherever they appear: `api_key`, `x-api-key`, `aws_access_key_id`, `accessToken`, `client_secret_value`. |
| [`SECRET_VALUE`](#ocracy.kit.translation.SECRET_VALUE)    | an auth scheme (`Bearer ...`), a URL carrying a user:password or a key-like query.                                                                                                                         |

### Functions

| [`make_translator`](#ocracy.kit.translation.make_translator)(param_map, \*[, backend, ...])   | Build `translate(kwargs, *, on_unsupported=None) -> Translation` from a map.   |
|---------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`check_range`](#ocracy.kit.translation.check_range)(name, value, spec)                   | Raise `ValueError` unless `value` fits `spec`'s `min`/`max`/`choices`.         |
| [`is_secret_name`](#ocracy.kit.translation.is_secret_name)(name)                             | Whether a parameter (or mapping key) named `name` may hold a secret.           |

### Classes

| [`Translation`](#ocracy.kit.translation.Translation)([kwargs, notes, dropped])   | What a translator produced: the native kwargs, and every change it made.   |
|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|

### Exceptions

| [`UnsupportedParameter`](#ocracy.kit.translation.UnsupportedParameter)   | A backend cannot honour a parameter, and the policy says not to drop it.   |
|-------------------------------------------------------------------------|----------------------------------------------------------------------------|

### ocracy.kit.translation.OUT_OF_RANGE *= ('raise', 'clamp', 'drop')*

How a value outside a spec’s `choices` / `min` / `max` is handled.

### ocracy.kit.translation.POLICIES *= ('raise', 'warn', 'note', 'ignore')*

How a parameter the backend cannot honour is handled.

### ocracy.kit.translation.SECRET_SEGMENTS *= frozenset({'apikey', 'auth', 'authorization', 'bearer', 'cookie', 'credential', 'credentials', 'key', 'passphrase', 'passwd', 'password', 'private', 'pwd', 'secret', 'session', 'sig', 'signature', 'token'})*

Name segments (split on `_ - .`, spaces and camelCase, case-insensitive) that
make a value secret wherever they appear: `api_key`, `x-api-key`,
`aws_access_key_id`, `accessToken`, `client_secret_value`. The rule errs
toward hiding: `key_frames` or a musical `key` are hidden too, which costs a
drop note its value and nothing else.

### ocracy.kit.translation.SECRET_VALUE *= re.compile('^\\\\s\*(bearer|basic|token)\\\\s+\\\\S|://[^/\\\\s:@]+:[^/\\\\s@]+@|[?&#](api_?key|key|token|access_token|auth|sig|signature|password)=', re.IGNORECASE)*

an auth
scheme (`Bearer ...`), a URL carrying a user:password or a key-like query.

* **Type:**
  String values that are credentials whatever the parameter is called

### *class* ocracy.kit.translation.Translation(kwargs=<factory>, notes=<factory>, dropped=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What a translator produced: the native kwargs, and every change it made.

#### kwargs

The native kwargs to pass to the backend.

#### notes

One human-readable line per drop or clamp, for the facade’s result.

#### dropped

The canonical names that were dropped.

### *exception* ocracy.kit.translation.UnsupportedParameter

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A backend cannot honour a parameter, and the policy says not to drop it.

### ocracy.kit.translation.check_range(name, value, spec)

Raise `ValueError` unless `value` fits `spec`’s `min`/`max`/`choices`.

The standalone form of the translator’s `out_of_range='raise'` check; returns
`value` unchanged. `None` is “unset” and always fits.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

### ocracy.kit.translation.is_secret_name(name)

Whether a parameter (or mapping key) named `name` may hold a secret.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.kit.translation.make_translator(param_map, , backend='', on_unsupported='warn', always_raise=(), vocabulary=None, passthrough=(), skip_none=False, out_of_range='raise', stacklevel=2)

Build `translate(kwargs, *, on_unsupported=None) -> Translation` from a map.

* **Parameters:**
  * **param_map** ([`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Canonical name -> spec (see the module docstring). Specs are
    validated here, so a malformed map fails when the backend loads, not on
    the first call that happens to use the bad entry.
  * **backend** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend’s name, used in notes and errors.
  * **on_unsupported** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend’s policy (one of [`POLICIES`](#ocracy.kit.translation.POLICIES)).
  * **always_raise** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Canonical names that raise under the backend’s policy because
    dropping them changes what the caller gets.
  * **vocabulary** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – The facade’s canonical names -> their default values. Enables
    “not asked for” detection and “not a parameter of” wording.
  * **passthrough** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Names passed through untranslated and unreported.
  * **skip_none** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Treat a `None` value as unset: never sent, never reported.
  * **out_of_range** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The default for specs that do not set their own.
  * **stacklevel** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – The frame a `'warn'` points at, counted from the code that
    calls `translate` (1 = that code, 2 = its caller).
* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Translation`](#ocracy.kit.translation.Translation)]
* **Returns:**
  `translate`. Its optional `on_unsupported=` is the *caller’s* policy for
  this one call; when given it replaces both the backend’s policy and
  `always_raise`.
