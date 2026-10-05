# ocracy.kit

The facade kit: the three helpers every fleet facade used to copy by hand.

One interface over many backends needs the same three mechanisms whatever the
backends do, and until this kit each facade (ocracy, scribed, denote, arioso,
illustration, aix, foley, falaw, voxy) carried its own drifting copy:

- [`translation`](ocracy.kit.translation.md#module-ocracy.kit.translation) – canonical kwargs -> native kwargs from a
  declared `param_map`, with an unsupported-parameter policy that never drops
  silently (every drop and clamp comes back as a note);
- [`credentials`](ocracy.kit.credentials.md#module-ocracy.kit.credentials) – the key chain (explicit -> bound in context ->
  env -> store -> prompt), whose error names the env vars and where to get a key;
- [`install`](ocracy.kit.install.md#module-ocracy.kit.install) – per-OS install plans an agent can act on.

Usage:

```default
from ocracy.kit import make_translator, resolve_credential, using_credentials

translate = make_translator(BACKEND_CONFIG["param_map"], backend="acme",
                            on_unsupported="note", always_raise=("seed",))
t = translate(canonical_kwargs)        # t.kwargs, t.notes, t.dropped
key = resolve_credential("acme", env_var="ACME_API_KEY", api_key=api_key)
```

Every module here is stdlib-only and imports nothing from ocracy outside
`ocracy.kit`, so the kit can move to its own distribution without a rewrite.
The decisions behind its shape are in `docs/adr/0001-facade-kit.md`.

### Functions

| [`make_translator`](#ocracy.kit.make_translator)(param_map, \*[, backend, ...])   | Build `translate(kwargs, *, on_unsupported=None) -> Translation` from a map.                                              |
|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| [`check_range`](#ocracy.kit.check_range)(name, value, spec)                   | Raise `ValueError` unless `value` fits `spec`'s `min`/`max`/`choices`.                                                    |
| [`resolve_credential`](#ocracy.kit.resolve_credential)([provider, api_key, ...])     | Resolve a provider's credential through the chain in the module docstring.                                                |
| [`using_credentials`](#ocracy.kit.using_credentials)([keys])                        | Bind provider keys for the `with` block (overlaying any outer binding).                                                   |
| [`current_credentials`](#ocracy.kit.current_credentials)()                            | The provider keys bound in this context by [`using_credentials()`](#ocracy.kit.using_credentials) (a copy). |
| [`env_var_names`](#ocracy.kit.env_var_names)([provider, env_var, ...])          | The env vars the chain checks: `env_var` first, then the provider's row.                                                  |
| [`credential_help`](#ocracy.kit.credential_help)(provider, \*[, guidance])        | A short, link-bearing "how to get a key" line for `provider` (or `''`).                                                   |
| [`credential_lines`](#ocracy.kit.credential_lines)(env_var, provider, \*[, ...])   | `export VAR  (get a key: URL)` lines for an install plan (empty if no var).                                               |
| [`build_requirements`](#ocracy.kit.build_requirements)(backend_id, \*, package, ...) | Build [`Requirements`](#ocracy.kit.Requirements) for `backend_id` from its recipe and known facts.     |
| [`run_install`](#ocracy.kit.run_install)(req, \*, package[, yes, ...])        | Plan (default) or run (`yes=True`) the pip install that `req` describes.                                                  |
| [`current_platform`](#ocracy.kit.current_platform)()                               | `'darwin'`, `'linux'`, `'windows'`, or `sys.platform` for anything else.                                                  |

### Classes

| [`Translation`](#ocracy.kit.Translation)([kwargs, notes, dropped])             | What a translator produced: the native kwargs, and every change it made.   |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`Requirements`](#ocracy.kit.Requirements)(backend_id, implemented, ...[, ...]) | What a backend needs to run, structured for an agent to act on.            |

### Exceptions

| [`UnsupportedParameter`](#ocracy.kit.UnsupportedParameter)                             | A backend cannot honour a parameter, and the policy says not to drop it.      |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`MissingCredentialError`](#ocracy.kit.MissingCredentialError)([message, provider, ...]) | A required credential could not be resolved; the message says how to get one. |

### *exception* ocracy.kit.MissingCredentialError(message='', , provider=None, env_vars=(), get_key_url=None)

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

A required credential could not be resolved; the message says how to get one.

#### provider

The provider id asked for (or `None`).

#### env_vars

The env vars that were checked, in order.

#### get_key_url

Where to get a key, when the guidance table knows.

### *class* ocracy.kit.Requirements(backend_id, implemented, available, is_local, is_remote, pip_command, extra=None, system=<factory>, system_note=None, gpu=None, weights=None, heavy=False, alternative=None, credentials=<factory>, notes=<factory>, verify_command=None, alternative_label='Lighter alternative')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What a backend needs to run, structured for an agent to act on.

#### instructions()

An agent- and human-readable, copy-pasteable install plan.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* ocracy.kit.Translation(kwargs=<factory>, notes=<factory>, dropped=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What a translator produced: the native kwargs, and every change it made.

#### kwargs

The native kwargs to pass to the backend.

#### notes

One human-readable line per drop or clamp, for the facade’s result.

#### dropped

The canonical names that were dropped.

### *exception* ocracy.kit.UnsupportedParameter

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A backend cannot honour a parameter, and the policy says not to drop it.

### ocracy.kit.build_requirements(backend_id, , package, implemented, available, recipe=None, is_local=False, is_remote=False, ledger_pip='', credentials=(), platform=None, verify_command=None, unimplemented_note=None, alternative_label='Lighter alternative')

Build [`Requirements`](#ocracy.kit.Requirements) for `backend_id` from its recipe and known facts.

* **Parameters:**
  * **backend_id** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend’s id.
  * **package** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The distribution whose extra installs it (`pip install "pkg[x]"`).
  * **implemented** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether the package ships a facade for it.
  * **available** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether it is usable right now (the package’s own probe).
  * **recipe** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)]) – Its row of the package’s recipes table (see the module docstring).
  * **is_remote** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – From the backend’s config or ledger record.
  * **ledger_pip** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The ledger’s install line, used for a backend not implemented.
  * **credentials** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – `export` lines (see [`credential_lines()`](ocracy.kit.credentials.md#ocracy.kit.credentials.credential_lines)).
  * **platform** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Override [`current_platform()`](#ocracy.kit.current_platform) (for tests and docs).
  * **verify_command** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – The shell line shown as `Verify:`.
  * **unimplemented_note** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Appended to `notes` when not implemented.
  * **alternative_label** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The wording before `alt` in the instructions.
* **Return type:**
  [`Requirements`](ocracy.kit.install.md#ocracy.kit.install.Requirements)

### ocracy.kit.check_range(name, value, spec)

Raise `ValueError` unless `value` fits `spec`’s `min`/`max`/`choices`.

The standalone form of the translator’s `out_of_range='raise'` check; returns
`value` unchanged. `None` is “unset” and always fits.

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

### ocracy.kit.credential_help(provider, , guidance=None)

A short, link-bearing “how to get a key” line for `provider` (or `''`).

`guidance[provider]` may carry `note` and `get_key_url`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.kit.credential_lines(env_var, provider, , guidance=None)

`export VAR  (get a key: URL)` lines for an install plan (empty if no var).

Several env vars (alternatives) are shown as `A / B`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.kit.current_credentials()

The provider keys bound in this context by [`using_credentials()`](#ocracy.kit.using_credentials) (a copy).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.kit.current_platform()

`'darwin'`, `'linux'`, `'windows'`, or `sys.platform` for anything else.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.kit.env_var_names(provider=None, , env_var=None, provider_env_vars=None)

The env vars the chain checks: `env_var` first, then the provider’s row.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.kit.make_translator(param_map, , backend='', on_unsupported='warn', always_raise=(), vocabulary=None, passthrough=(), skip_none=False, out_of_range='raise', stacklevel=2)

Build `translate(kwargs, *, on_unsupported=None) -> Translation` from a map.

* **Parameters:**
  * **param_map** ([`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Canonical name -> spec (see the module docstring). Specs are
    validated here, so a malformed map fails when the backend loads, not on
    the first call that happens to use the bad entry.
  * **backend** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend’s name, used in notes and errors.
  * **on_unsupported** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The backend’s policy (one of `POLICIES`).
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
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Translation`](ocracy.kit.translation.md#ocracy.kit.translation.Translation)]
* **Returns:**
  `translate`. Its optional `on_unsupported=` is the *caller’s* policy for
  this one call; when given it replaces both the backend’s policy and
  `always_raise`.

### ocracy.kit.resolve_credential(provider=None, \*, api_key=None, env_var=None, provider_env_vars=None, guidance=None, store=None, dotenv=False, prompt_if_missing=False, required=True, error=<class 'ocracy.kit.credentials.MissingCredentialError'>, hint='')

Resolve a provider’s credential through the chain in the module docstring.

* **Parameters:**
  * **provider** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – The provider id, used for bindings, table rows and messages.
  * **api_key** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – An explicit value; wins when non-empty.
  * **env_var** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Env var name(s) checked before the provider’s table row.
  * **provider_env_vars** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), `Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]]]) – The package’s provider -> env var(s) table.
  * **guidance** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)]) – The package’s provider -> `{note, get_key_url}` table.
  * **store** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]) – A mapping keyed by env-var name, read after the environment.
  * **dotenv** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – On an environment miss, load a project `.env` (searched from the
    current directory, never overriding) and look again.
  * **prompt_if_missing** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Ask with `getpass` when interactive (last resort).
  * **required** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Raise when nothing resolves; else return `None`.
  * **error** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`BaseException`](https://docs.python.org/3/builtins/exceptions.html#BaseException)]) – The exception to raise, called with the message. When it builds a
    [`MissingCredentialError`](#ocracy.kit.MissingCredentialError) (or subclass), its `provider`,
    `env_vars` and `get_key_url` attributes are filled in.
  * **hint** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – An extra sentence for the error message (why this key is needed).
* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  The secret, or `None` when `required=False` and nothing resolved.

### ocracy.kit.run_install(req, , package, yes=False, verify_code=None, upgrade=False)

Plan (default) or run (`yes=True`) the pip install that `req` describes.

* **Parameters:**
  * **req** ([`Requirements`](ocracy.kit.install.md#ocracy.kit.install.Requirements)) – The plan, from [`build_requirements()`](#ocracy.kit.build_requirements).
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

### ocracy.kit.using_credentials(keys=None, , \*\*provider_keys)

Bind provider keys for the `with` block (overlaying any outer binding).

Pass a mapping for provider ids that are not identifiers (`"google-vision"`)
or keywords for the rest. Falsy values are ignored, so an optional request
header can be passed straight through.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

```pycon
>>> with using_credentials(acme="outer"):
...     with using_credentials({"acme": "inner", "other": None}):
...         inner = current_credentials()
...     outer = current_credentials()
>>> inner, outer
({'acme': 'inner'}, {'acme': 'outer'})
```

### Modules

| [`credentials`](ocracy.kit.credentials.md#module-ocracy.kit.credentials)   | One credential chain for every facade: explicit -> bound -> env -> store -> prompt.   |
|----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`install`](ocracy.kit.install.md#module-ocracy.kit.install)           | Install plans: what a backend needs on *this* OS, as data an agent can act on.        |
| [`translation`](ocracy.kit.translation.md#module-ocracy.kit.translation)   | Canonical -> native keyword translation, with an honest unsupported-parameter policy. |
