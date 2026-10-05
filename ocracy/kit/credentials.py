"""One credential chain for every facade: explicit -> bound -> env -> store -> prompt.

:func:`resolve_credential` looks for a provider's secret in this order and stops at
the first non-empty value:

1. ``api_key=`` passed by the caller (an empty string counts as not given);
2. a key bound for this provider in the current context with
   :func:`using_credentials` -- the bring-your-own-key seam a server uses without
   threading a key through every call;
3. the environment: ``env_var`` first, then the provider's row of
   ``provider_env_vars``, in order, without duplicates (with ``dotenv=True`` a
   project ``.env``, found from the current directory, is loaded first -- once per
   directory -- and never overrides a variable that is already set; like any
   ``.env`` loader it writes to ``os.environ``, so every later reader sees it);
4. ``store``: any mapping keyed by env-var name (a ``config2py`` store, a dict);
   only a missing key moves on, any other error propagates;
5. with ``prompt_if_missing=True`` and an interactive terminal, ``getpass``; the
   answer is written to ``store`` when it is a ``MutableMapping``, else to the
   process environment.

When nothing resolves and ``required=True``, it raises ``error`` (default
:class:`MissingCredentialError`) with a message naming every env var it tried and,
from ``guidance``, where to get a key::

    >>> resolve_credential("acme", api_key="explicit")
    'explicit'
    >>> with using_credentials(acme="bound"):
    ...     resolve_credential("acme")
    'bound'
    >>> resolve_credential("acme", env_var="ACME_SURELY_UNSET_KEY", required=False) is None
    True

Two properties of the binding (step 2) that a server must know:

- **It is shared by provider id across every package using the kit.** A key bound
  as ``openai`` reaches ocracy, aix and any other facade calling OpenAI in that
  context. That is the point of a bring-your-own-key binding, so pick provider ids
  that name the *account* (``openai``, ``fal``, ``elevenlabs``), not the facade.
- **It is a** :class:`~contextvars.ContextVar` **binding**, so it follows the
  context: ``asyncio`` tasks and ``asyncio.to_thread`` see it, but a bare
  ``threading.Thread``, ``ThreadPoolExecutor.submit`` or ``loop.run_in_executor``
  start from an empty context and fall through to the environment (the operator's
  key). Submit ``contextvars.copy_context().run`` to keep the binding.

A package binds its own tables once, with :func:`functools.partial` or a thin
wrapper, and keeps its public names; ocracy's :mod:`ocracy.credentials` is the
worked example. Stdlib only; imports nothing else from ocracy.
"""

from __future__ import annotations

import contextlib
import os
import sys
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Callable, Iterator, Mapping, Optional, Sequence, Union

__all__ = [
    "MissingCredentialError",
    "resolve_credential",
    "env_var_names",
    "credential_help",
    "credential_lines",
    "using_credentials",
    "current_credentials",
]

EnvVars = Union[str, Sequence[str], None]

#: Keys bound by :func:`using_credentials`, provider -> key. Replaced, never mutated.
_BOUND: "ContextVar[Optional[Mapping[str, str]]]" = ContextVar(
    "ocracy_kit_bound_credentials", default=None
)

#: The directories a ``.env`` search already ran from (see ``dotenv=``).
_dotenv_loaded_from: set = set()


class MissingCredentialError(RuntimeError):
    """A required credential could not be resolved; the message says how to get one.

    Attributes:
        provider: The provider id asked for (or ``None``).
        env_vars: The env vars that were checked, in order.
        get_key_url: Where to get a key, when the guidance table knows.
    """

    def __init__(
        self,
        message: str = "",
        *,
        provider: Optional[str] = None,
        env_vars: Sequence[str] = (),
        get_key_url: Optional[str] = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.env_vars = tuple(env_vars)
        self.get_key_url = get_key_url


def current_credentials() -> dict:
    """The provider keys bound in this context by :func:`using_credentials` (a copy)."""
    return dict(_BOUND.get() or {})


@contextlib.contextmanager
def using_credentials(
    keys: Optional[Mapping[str, Optional[str]]] = None,
    /,
    **provider_keys: Optional[str],
) -> Iterator[dict]:
    """Bind provider keys for the ``with`` block (overlaying any outer binding).

    Pass a mapping for provider ids that are not identifiers (``"google-vision"``)
    or keywords for the rest. Falsy values are ignored, so an optional request
    header can be passed straight through.

    >>> with using_credentials(acme="outer"):
    ...     with using_credentials({"acme": "inner", "other": None}):
    ...         inner = current_credentials()
    ...     outer = current_credentials()
    >>> inner, outer
    ({'acme': 'inner'}, {'acme': 'outer'})
    """
    merged = current_credentials()
    merged.update({k: v for k, v in {**dict(keys or {}), **provider_keys}.items() if v})
    token = _BOUND.set(merged)
    try:
        yield dict(merged)
    finally:
        _BOUND.reset(token)


def env_var_names(
    provider: Optional[str] = None,
    *,
    env_var: EnvVars = None,
    provider_env_vars: Optional[Mapping[str, EnvVars]] = None,
) -> list:
    """The env vars the chain checks: ``env_var`` first, then the provider's row."""
    names = _as_list(env_var)
    if provider and provider_env_vars and provider in provider_env_vars:
        names.extend(_as_list(provider_env_vars[provider]))
    return list(dict.fromkeys(names))


def credential_help(provider: str, *, guidance: Optional[Mapping] = None) -> str:
    """A short, link-bearing "how to get a key" line for ``provider`` (or ``''``).

    ``guidance[provider]`` may carry ``note`` and ``get_key_url``.
    """
    g = (guidance or {}).get(provider)
    if not g:
        return ""
    note = f" {g['note']}" if g.get("note") else ""
    url = f" Get a key: {g['get_key_url']}" if g.get("get_key_url") else ""
    return f"How to get a credential for {provider}:{note}{url}"


def credential_lines(
    env_var: EnvVars, provider: str, *, guidance: Optional[Mapping] = None
) -> list:
    """``export VAR  (get a key: URL)`` lines for an install plan (empty if no var).

    Several env vars (alternatives) are shown as ``A / B``.
    """
    names = _as_list(env_var)
    if not names:
        return []
    g = (guidance or {}).get(provider)
    link = f"  (get a key: {g['get_key_url']})" if g and g.get("get_key_url") else ""
    return [f"export {' / '.join(names)}{link}"]


def resolve_credential(
    provider: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    env_var: EnvVars = None,
    provider_env_vars: Optional[Mapping[str, EnvVars]] = None,
    guidance: Optional[Mapping] = None,
    store: Optional[Mapping[str, str]] = None,
    dotenv: bool = False,
    prompt_if_missing: bool = False,
    required: bool = True,
    error: Callable[[str], BaseException] = MissingCredentialError,
    hint: str = "",
) -> Optional[str]:
    """Resolve a provider's credential through the chain in the module docstring.

    Args:
        provider: The provider id, used for bindings, table rows and messages.
        api_key: An explicit value; wins when non-empty.
        env_var: Env var name(s) checked before the provider's table row.
        provider_env_vars: The package's provider -> env var(s) table.
        guidance: The package's provider -> ``{note, get_key_url}`` table.
        store: A mapping keyed by env-var name, read after the environment.
        dotenv: Load a project ``.env`` (searched from the current directory, once
            per directory), never overriding a variable already set.
        prompt_if_missing: Ask with ``getpass`` when interactive (last resort).
        required: Raise when nothing resolves; else return ``None``.
        error: The exception to raise, called with the message. A subclass of
            :class:`MissingCredentialError` also gets ``provider``, ``env_vars`` and
            ``get_key_url`` as keyword arguments.
        hint: An extra sentence for the error message (why this key is needed).

    Returns:
        The secret, or ``None`` when ``required=False`` and nothing resolved.
    """
    if api_key:
        return api_key
    if provider:
        bound = (_BOUND.get() or {}).get(provider)
        if bound:
            return bound
    names = env_var_names(
        provider, env_var=env_var, provider_env_vars=provider_env_vars
    )
    if dotenv:
        _load_dotenv_once()
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    if store is not None:
        for name in names:
            value = _store_get(store, name)
            if value:
                return value
    if prompt_if_missing:
        value = _prompt(names, provider, store)
        if value:
            return value
    if required:
        message = _missing_message(provider, names, guidance, hint)
        if isinstance(error, type) and issubclass(error, MissingCredentialError):
            url = ((guidance or {}).get(provider) or {}).get("get_key_url")
            raise error(message, provider=provider, env_vars=names, get_key_url=url)
        raise error(message)
    return None


def _as_list(env_var: EnvVars) -> list:
    if not env_var:
        return []
    return [env_var] if isinstance(env_var, str) else list(env_var)


def _store_get(store: Mapping[str, str], name: str) -> Optional[str]:
    try:
        value = store[name]
    except KeyError:
        return None
    return value.strip() if isinstance(value, str) else value


def _load_dotenv_once() -> None:
    """Load the ``.env`` found from the cwd, once per cwd, if dotenv is installed."""
    cwd = os.getcwd()
    if cwd in _dotenv_loaded_from:
        return
    try:
        from dotenv import find_dotenv, load_dotenv  # type: ignore
    except ImportError:
        return
    _dotenv_loaded_from.add(cwd)
    path = find_dotenv(usecwd=True)
    if path:
        load_dotenv(path, override=False)


def _prompt(names: list, provider: Optional[str], store) -> Optional[str]:
    if sys.stdin is None or not sys.stdin.isatty():
        return None
    import getpass

    label = names[0] if names else (provider or "API key")
    value = getpass.getpass(f"Enter credential for {label}: ").strip()
    if value and names:
        if isinstance(store, MutableMapping):
            store[names[0]] = value
        else:
            os.environ[names[0]] = value
    return value or None


def _missing_message(provider, names, guidance, hint) -> str:
    tried = f" (set one of: {', '.join(names)})" if names else ""
    message = f"No credential found for {provider or 'backend'}{tried}."
    if hint:
        message += f" {hint}"
    help_line = credential_help(provider, guidance=guidance) if provider else ""
    if help_line:
        message += "\n" + help_line
    return message
