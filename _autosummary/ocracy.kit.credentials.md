# ocracy.kit.credentials

One credential chain for every facade: explicit -> bound -> env -> store -> prompt.

[`resolve_credential()`](#ocracy.kit.credentials.resolve_credential) looks for a provider’s secret in this order and stops at
the first non-empty value:

1. `api_key=` passed by the caller (an empty string counts as not given);
2. a key bound for this provider in the current context with
   [`using_credentials()`](#ocracy.kit.credentials.using_credentials) – the bring-your-own-key seam a server uses without
   > threading a key through every call;
3. the environment: `env_var` first, then the provider’s row of
   `provider_env_vars`, in order, without duplicates (with `dotenv=True` a
   project `.env`, found from the current directory, is loaded on a miss and the
   environment checked again; it never overrides a variable that is already set,
   and like any `.env` loader it writes to `os.environ`, so every later reader
   sees it);
4. `store`: any mapping keyed by env-var name (a `config2py` store, a dict);
   only a missing key moves on, any other error propagates;
5. with `prompt_if_missing=True` and an interactive terminal, `getpass`; the
   answer is written to `store` when it is a `MutableMapping`, else to the
   process environment.

When nothing resolves and `required=True`, it raises `error` (default
[`MissingCredentialError`](#ocracy.kit.credentials.MissingCredentialError)) with a message naming every env var it tried and,
from `guidance`, where to get a key:

```default
>>> resolve_credential("acme", api_key="explicit")
'explicit'
>>> with using_credentials(acme="bound"):
...     resolve_credential("acme")
'bound'
>>> resolve_credential("acme", env_var="ACME_SURELY_UNSET_KEY", required=False) is None
True
```

Two properties of the binding (step 2) that a server must know:

- **It is shared by provider id across every package using the kit.** A key bound
  as `openai` reaches ocracy, aix and any other facade calling OpenAI in that
  context. That is the point of a bring-your-own-key binding, so pick provider ids
  that name the *account* (`openai`, `fal`, `elevenlabs`), not the facade.
- **It is a** [`ContextVar`](https://docs.python.org/3/library/contextvars.html#contextvars.ContextVar) **binding**, so it follows the
  context: `asyncio` tasks and `asyncio.to_thread` see it, but a bare
  `threading.Thread`, `ThreadPoolExecutor.submit` or `loop.run_in_executor`
  start from an empty context and fall through to the environment (the operator’s
  key). Submit `contextvars.copy_context().run` to keep the binding.

A package binds its own tables once, with [`functools.partial()`](https://docs.python.org/3/library/functools.html#functools.partial) or a thin
wrapper, and keeps its public names; ocracy’s [`ocracy.credentials`](ocracy.credentials.md#module-ocracy.credentials) is the
worked example. Stdlib only; imports nothing else from ocracy.

### Functions

| [`resolve_credential`](#ocracy.kit.credentials.resolve_credential)([provider, api_key, ...])   | Resolve a provider's credential through the chain in the module docstring.                                                |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| [`env_var_names`](#ocracy.kit.credentials.env_var_names)([provider, env_var, ...])        | The env vars the chain checks: `env_var` first, then the provider's row.                                                  |
| [`credential_help`](#ocracy.kit.credentials.credential_help)(provider, \*[, guidance])      | A short, link-bearing "how to get a key" line for `provider` (or `''`).                                                   |
| [`credential_lines`](#ocracy.kit.credentials.credential_lines)(env_var, provider, \*[, ...]) | `export VAR  (get a key: URL)` lines for an install plan (empty if no var).                                               |
| [`using_credentials`](#ocracy.kit.credentials.using_credentials)([keys])                      | Bind provider keys for the `with` block (overlaying any outer binding).                                                   |
| [`current_credentials`](#ocracy.kit.credentials.current_credentials)()                          | The provider keys bound in this context by [`using_credentials()`](#ocracy.kit.credentials.using_credentials) (a copy). |

### Exceptions

| [`MissingCredentialError`](#ocracy.kit.credentials.MissingCredentialError)([message, provider, ...])   | A required credential could not be resolved; the message says how to get one.   |
|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|

### *exception* ocracy.kit.credentials.MissingCredentialError(message='', , provider=None, env_vars=(), get_key_url=None)

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

A required credential could not be resolved; the message says how to get one.

#### provider

The provider id asked for (or `None`).

#### env_vars

The env vars that were checked, in order.

#### get_key_url

Where to get a key, when the guidance table knows.

### ocracy.kit.credentials.credential_help(provider, , guidance=None)

A short, link-bearing “how to get a key” line for `provider` (or `''`).

`guidance[provider]` may carry `note` and `get_key_url`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.kit.credentials.credential_lines(env_var, provider, , guidance=None)

`export VAR  (get a key: URL)` lines for an install plan (empty if no var).

Several env vars (alternatives) are shown as `A / B`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.kit.credentials.current_credentials()

The provider keys bound in this context by [`using_credentials()`](#ocracy.kit.credentials.using_credentials) (a copy).

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### ocracy.kit.credentials.env_var_names(provider=None, , env_var=None, provider_env_vars=None)

The env vars the chain checks: `env_var` first, then the provider’s row.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)

### ocracy.kit.credentials.resolve_credential(provider=None, \*, api_key=None, env_var=None, provider_env_vars=None, guidance=None, store=None, dotenv=False, prompt_if_missing=False, required=True, error=<class 'ocracy.kit.credentials.MissingCredentialError'>, hint='')

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
    [`MissingCredentialError`](#ocracy.kit.credentials.MissingCredentialError) (or subclass), its `provider`,
    `env_vars` and `get_key_url` attributes are filled in.
  * **hint** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – An extra sentence for the error message (why this key is needed).
* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  The secret, or `None` when `required=False` and nothing resolved.

### ocracy.kit.credentials.using_credentials(keys=None, , \*\*provider_keys)

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
