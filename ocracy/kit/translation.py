"""Canonical -> native keyword translation, with an honest unsupported-parameter policy.

A facade speaks one vocabulary (``languages``, ``duration``, ``seed``); each backend
speaks its own (``lang``, ``audio_length_s``, ``random_seed``). A backend declares a
``param_map`` from canonical names to *specs*, and :func:`make_translator` turns it
into a function that rewrites the caller's canonical kwargs into native ones and
**reports every change** it made::

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

A spec is one of:

- ``None`` -- the backend explicitly does not support the parameter;
- a ``str`` -- a plain rename to that native name;
- a callable -- coerce the value, keep the canonical name;
- a mapping with any of: ``native_name`` (``name`` is accepted as an alias),
  ``coerce``, ``default`` (injected when the caller omits the parameter),
  ``choices`` / ``min`` / ``max`` (checked on the *canonical* value), and
  ``out_of_range`` -- ``'raise'``, ``'clamp'`` (``min``/``max`` only, with a note) or
  ``'drop'`` (handled like an unsupported parameter); the translator's
  ``out_of_range=`` is the default -- plus ``unit`` (shown in the clamp note).
  ``native_name: None`` means unsupported, exactly like a bare ``None``.
  ``adapter_handled: True`` passes the value through under its canonical name, for
  the adapter to handle (whatever ``native_name`` says). Other keys
  (``description``...) are ignored.

The policy for a parameter the backend cannot honour is one of :data:`POLICIES`:
``'raise'`` (:class:`UnsupportedParameter`), ``'warn'`` (drop, note it, and
:func:`warnings.warn`), ``'note'`` (drop and note it), or ``'ignore'`` (an alias of
``'note'``: kept for the copies that used it, and still never silent -- the drop is
always in :attr:`Translation.notes` and :attr:`Translation.dropped`).

Notes and warnings show the dropped value, shortened, so a reader knows what was
lost -- except for a parameter whose name looks like a secret (``api_key``,
``token``, ``password``...), whose value is never shown: notes end up in results
that get stored and logged.

Several choices are declared once, when the translator is made, and each was a real
divergence between the fleet's copies (see ``docs/adr/0001-facade-kit.md``):

- ``always_raise`` -- parameters that *carry meaning* (``lyrics``, ``seed``,
  ``negative_prompt``): dropping them changes what the caller gets, so they raise
  under the backend's policy. A caller who passes ``on_unsupported=`` to the
  translator call has chosen explicitly, and that choice wins.
- ``vocabulary`` -- the facade's canonical names mapped to their defaults. With it,
  an unsupported parameter left at its default (or ``None``) was never asked for, so
  it is skipped rather than reported as dropped, and an unknown name is worded
  "not a parameter of" rather than "not supported by".
- ``skip_none`` / ``passthrough`` -- a ``None`` value means "unset" and is never sent;
  named adapter-only parameters (credentials, clients) go through untranslated.
- ``stacklevel`` -- which frame a ``'warn'`` points at, counted from the code that
  calls the translator (1 = that code, 2 = its caller...).

Stdlib only; imports nothing else from ocracy.
"""

from __future__ import annotations

import re
import reprlib
import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Mapping, Optional

__all__ = [
    "POLICIES",
    "OUT_OF_RANGE",
    "UnsupportedParameter",
    "Translation",
    "make_translator",
    "check_range",
    "SECRET_NAME",
]

#: How a parameter the backend cannot honour is handled.
POLICIES = ("raise", "warn", "note", "ignore")

#: How a value outside a spec's ``choices`` / ``min`` / ``max`` is handled.
OUT_OF_RANGE = ("raise", "clamp", "drop")

#: Parameter names whose values never appear in a note, a warning or an error.
SECRET_NAME = re.compile(
    r"(^|_)(api_?key|app_?key|key|token|secret|password|passwd|credentials?|auth)($|_)",
    re.IGNORECASE,
)

_DEFAULT_WHERE = "this backend"
_FRAMES_BELOW_CALLER = 2  # _drop -> translate -> (the code calling translate)
_VALUE_REPR = reprlib.Repr()
_VALUE_REPR.maxstring = _VALUE_REPR.maxother = 80


class UnsupportedParameter(ValueError):
    """A backend cannot honour a parameter, and the policy says not to drop it."""


@dataclass
class Translation:
    """What a translator produced: the native kwargs, and every change it made.

    Attributes:
        kwargs: The native kwargs to pass to the backend.
        notes: One human-readable line per drop or clamp, for the facade's result.
        dropped: The canonical names that were dropped.
    """

    kwargs: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    dropped: list = field(default_factory=list)


_MISSING = object()


@dataclass(frozen=True)
class _Spec:
    native_name: str
    coerce: Optional[Callable[[Any], Any]] = None
    default: Any = _MISSING
    choices: Any = None
    min: Any = None
    max: Any = None
    out_of_range: str = "raise"
    unit: str = ""


def _check_out_of_range(value: Any, where: str) -> None:
    if value not in OUT_OF_RANGE:
        raise ValueError(f"{where} must be one of {OUT_OF_RANGE}, got {value!r}")


def _parse_spec(
    name: str, spec: Any, *, out_of_range: str = "raise"
) -> Optional[_Spec]:
    """Normalize one ``param_map`` value; ``None`` means unsupported."""
    if spec is None:
        return None
    if isinstance(spec, str):
        return _Spec(native_name=spec)
    if isinstance(spec, Mapping):
        if spec.get("adapter_handled"):
            return _Spec(native_name=name)
        if "native_name" in spec and "name" in spec:
            if spec["native_name"] != spec["name"]:
                raise TypeError(
                    f"param_map[{name!r}] gives both native_name={spec['native_name']!r} "
                    f"and name={spec['name']!r}; use native_name only."
                )
        native = spec.get("native_name", spec.get("name", name))
        if native is None:
            return None
        spec_range = spec.get("out_of_range", out_of_range)
        _check_out_of_range(spec_range, f"param_map[{name!r}]['out_of_range']")
        if spec_range == "clamp" and spec.get("choices") is not None:
            raise ValueError(
                f"param_map[{name!r}]: out_of_range='clamp' needs min/max, not choices"
            )
        return _Spec(
            native_name=native,
            coerce=spec.get("coerce"),
            default=spec.get("default", _MISSING),
            choices=spec.get("choices"),
            min=spec.get("min"),
            max=spec.get("max"),
            out_of_range=spec_range,
            unit=spec.get("unit") or "",
        )
    if callable(spec):
        return _Spec(native_name=name, coerce=spec)
    raise TypeError(f"Invalid param_map spec for {name!r}: {spec!r}")


def _check_policy(policy: Optional[str], *, allow_none: bool = False) -> None:
    if policy is None and allow_none:
        return
    if policy not in POLICIES:
        raise ValueError(f"on_unsupported must be one of {POLICIES}, got {policy!r}")


def _shown(name: str, value: Any) -> str:
    """``name=<short repr>``, or ``name=<redacted>`` for a secret-looking name."""
    if SECRET_NAME.search(name):
        return f"{name}=<redacted>"
    try:
        return f"{name}={_VALUE_REPR.repr(value)}"
    except Exception:  # noqa: BLE001 - a value whose repr fails is still reportable
        return f"{name}=<{type(value).__name__}>"


def check_range(name: str, value: Any, spec: Mapping) -> Any:
    """Raise ``ValueError`` unless ``value`` fits ``spec``'s ``min``/``max``/``choices``.

    The standalone form of the translator's ``out_of_range='raise'`` check; returns
    ``value`` unchanged. ``None`` is "unset" and always fits.
    """
    _raise_if_out_of_range(name, value, _parse_spec(name, dict(spec)) or _Spec(name))
    return value


def _range_problem(value: Any, spec: _Spec) -> Optional[str]:
    """Which bound ``value`` breaks: ``'min'``, ``'max'``, ``'choices'`` or ``None``.

    A ``None`` value breaks nothing: it means "unset", and the backend decides.
    """
    if value is None:
        return None
    if spec.min is not None and value < spec.min:
        return "min"
    if spec.max is not None and value > spec.max:
        return "max"
    if spec.choices is not None and value not in spec.choices:
        return "choices"
    return None


def _raise_if_out_of_range(name: str, value: Any, spec: _Spec) -> None:
    problem = _range_problem(value, spec)
    if problem == "min":
        raise ValueError(
            f"Parameter {name!r} value {value} is below minimum {spec.min}"
        )
    if problem == "max":
        raise ValueError(
            f"Parameter {name!r} value {value} is above maximum {spec.max}"
        )
    if problem == "choices":
        raise ValueError(f"Parameter {name!r} value {value!r} not in {spec.choices}")


def make_translator(
    param_map: Mapping[str, Any],
    *,
    backend: str = "",
    on_unsupported: str = "warn",
    always_raise: Iterable[str] = (),
    vocabulary: Optional[Mapping[str, Any]] = None,
    passthrough: Iterable[str] = (),
    skip_none: bool = False,
    out_of_range: str = "raise",
    stacklevel: int = 2,
) -> Callable[..., Translation]:
    """Build ``translate(kwargs, *, on_unsupported=None) -> Translation`` from a map.

    Args:
        param_map: Canonical name -> spec (see the module docstring). Specs are
            validated here, so a malformed map fails when the backend loads, not on
            the first call that happens to use the bad entry.
        backend: The backend's name, used in notes and errors.
        on_unsupported: The backend's policy (one of :data:`POLICIES`).
        always_raise: Canonical names that raise under the backend's policy because
            dropping them changes what the caller gets.
        vocabulary: The facade's canonical names -> their default values. Enables
            "not asked for" detection and "not a parameter of" wording.
        passthrough: Names passed through untranslated and unreported.
        skip_none: Treat a ``None`` value as unset: never sent, never reported.
        out_of_range: The default for specs that do not set their own.
        stacklevel: The frame a ``'warn'`` points at, counted from the code that
            calls ``translate`` (1 = that code, 2 = its caller).

    Returns:
        ``translate``. Its optional ``on_unsupported=`` is the *caller's* policy for
        this one call; when given it replaces both the backend's policy and
        ``always_raise``.
    """
    _check_policy(on_unsupported)
    _check_out_of_range(out_of_range, "out_of_range")
    specs = {
        name: _parse_spec(name, spec, out_of_range=out_of_range)
        for name, spec in param_map.items()
    }
    supported = sorted(n for n, s in specs.items() if s is not None)
    raising = frozenset(always_raise)
    passing = frozenset(passthrough)
    vocab = dict(vocabulary) if vocabulary is not None else None
    where = backend or _DEFAULT_WHERE
    default_policy = on_unsupported
    warn_stacklevel = _FRAMES_BELOW_CALLER + stacklevel

    def _not_asked_for(name: str, value: Any) -> bool:
        if vocab is None:
            return False
        if value is None:
            return True
        default = vocab.get(name)
        try:
            return default is not None and bool(value == default)
        except Exception:  # noqa: BLE001 - an uncomparable value was asked for
            return False

    def _kind(name: str) -> str:
        known = name in specs or (vocab is not None and name in vocab)
        return "not supported by" if known else "not a parameter of"

    def _drop(name, value, policy, call_policy, out: Translation, *, reason=None):
        what = f"{_shown(name, value)} {reason or 'is ' + _kind(name) + ' ' + where}"
        if policy == "raise":
            changes_meaning = call_policy is None and name in raising
            detail = (
                ", and dropping it would change what you get"
                if changes_meaning
                else f". Supported: {supported}"
            )
            raise UnsupportedParameter(
                f"{what}{detail}. Remove it, pick a backend that supports it, or pass "
                "on_unsupported='note' to drop it with a note."
            )
        message = f"{what}; dropped"
        if policy == "warn":
            warnings.warn(message, UserWarning, stacklevel=warn_stacklevel)
        out.notes.append(message)
        out.dropped.append(name)

    def translate(
        kwargs: Optional[Mapping[str, Any]] = None,
        /,
        *,
        on_unsupported: Optional[str] = None,
    ) -> Translation:
        """Translate canonical ``kwargs`` for this backend (see :func:`make_translator`)."""
        _check_policy(on_unsupported, allow_none=True)
        call_policy = on_unsupported

        def policy_for(name: str) -> str:
            if call_policy is not None:
                return call_policy
            return "raise" if name in raising else default_policy

        out = Translation()
        for name, value in dict(kwargs or {}).items():
            if skip_none and value is None:
                continue
            if name in passing:
                out.kwargs[name] = value
                continue
            spec = specs.get(name, _MISSING)
            if spec is _MISSING or spec is None:
                if not _not_asked_for(name, value):
                    _drop(name, value, policy_for(name), call_policy, out)
                continue
            problem = _range_problem(value, spec)
            if problem is not None:
                if spec.out_of_range == "raise":
                    _raise_if_out_of_range(name, value, spec)
                if spec.out_of_range == "drop":
                    bound = (
                        spec.choices
                        if problem == "choices"
                        else f"[{spec.min}, {spec.max}]"
                    )
                    reason = f"is outside {where}'s {bound}"
                    _drop(
                        name, value, policy_for(name), call_policy, out, reason=reason
                    )
                    continue
                value = _clamp(name, value, spec, where, out)
            if spec.coerce is not None:
                value = spec.coerce(value)
            out.kwargs[spec.native_name] = value
        for spec in specs.values():
            if spec is not None and spec.default is not _MISSING:
                out.kwargs.setdefault(spec.native_name, spec.default)
        return out

    return translate


def _clamp(name: str, value: Any, spec: _Spec, where: str, out: Translation) -> Any:
    """Clamp ``value`` into ``[spec.min, spec.max]`` and note it."""
    clamped = value
    if spec.min is not None and clamped < spec.min:
        clamped = spec.min
    if spec.max is not None and clamped > spec.max:
        clamped = spec.max
    unit = f" {spec.unit}" if spec.unit else ""
    try:
        shown = f"{clamped:g}"
    except (TypeError, ValueError):
        shown = repr(clamped)
    out.notes.append(
        f"{_shown(name, value)}{unit} is outside {where}'s [{spec.min}, {spec.max}]"
        f"{unit} window; clamped to {shown}{unit}"
    )
    return clamped
