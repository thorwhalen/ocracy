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
    >>> native, notes = t                         # a Translation unpacks to two

A spec is one of:

- ``None`` -- the backend explicitly does not support the parameter;
- a ``str`` -- a plain rename to that native name;
- a callable -- coerce the value, keep the canonical name;
- a mapping with any of: ``native_name`` (``name`` is accepted as an alias),
  ``coerce``, ``default`` (injected when the caller omits the parameter),
  ``choices`` / ``min`` / ``max`` (checked on the *canonical* value), and
  ``out_of_range`` -- ``'raise'`` (default), ``'clamp'`` (``min``/``max`` only, with a
  note) or ``'drop'`` (handled like an unsupported parameter) -- plus ``unit`` (shown
  in the clamp note). ``native_name: None`` means unsupported, exactly like a bare
  ``None``. Unknown keys (``description``, ``adapter_handled``...) are ignored.

The policy for a parameter the backend cannot honour is one of :data:`POLICIES`:
``'raise'`` (:class:`UnsupportedParameter`), ``'warn'`` (drop, note it, and
:func:`warnings.warn`), ``'note'`` (drop and note it), or ``'ignore'`` (an alias of
``'note'``: kept for the copies that used it, and still never silent -- the drop is
always in :attr:`Translation.notes` and :attr:`Translation.dropped`).

Three choices are declared once, when the translator is made, and each was a real
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
  named adapter-only parameters go through untranslated.

Stdlib only; imports nothing else from ocracy.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Iterator, Mapping, Optional

__all__ = [
    "POLICIES",
    "OUT_OF_RANGE",
    "UnsupportedParameter",
    "Translation",
    "make_translator",
    "check_range",
]

#: How a parameter the backend cannot honour is handled.
POLICIES = ("raise", "warn", "note", "ignore")

#: How a value outside a spec's ``choices`` / ``min`` / ``max`` is handled.
OUT_OF_RANGE = ("raise", "clamp", "drop")

_DEFAULT_WHERE = "this backend"
_WARN_STACKLEVEL = 4  # _drop -> translate -> the adapter calling it -> its caller


class UnsupportedParameter(ValueError):
    """A backend cannot honour a parameter, and the policy says not to drop it."""


@dataclass
class Translation:
    """What a translator produced: the native kwargs, and every change it made.

    Iterating gives ``(kwargs, notes)``, so ``native, notes = translate(kw)`` works.

    Attributes:
        kwargs: The native kwargs to pass to the backend.
        notes: One human-readable line per drop or clamp, for the facade's result.
        dropped: The canonical names that were dropped.
    """

    kwargs: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)
    dropped: list = field(default_factory=list)

    def __iter__(self) -> Iterator:
        return iter((self.kwargs, self.notes))


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


def _parse_spec(name: str, spec: Any) -> Optional[_Spec]:
    """Normalize one ``param_map`` value; ``None`` means unsupported."""
    if spec is None:
        return None
    if isinstance(spec, str):
        return _Spec(native_name=spec)
    if isinstance(spec, Mapping):
        if "native_name" in spec and "name" in spec:
            if spec["native_name"] != spec["name"]:
                raise TypeError(
                    f"param_map[{name!r}] gives both native_name={spec['native_name']!r} "
                    f"and name={spec['name']!r}; use native_name only."
                )
        native = spec.get("native_name", spec.get("name", name))
        if native is None:
            return None
        out_of_range = spec.get("out_of_range", "raise")
        if out_of_range not in OUT_OF_RANGE:
            raise ValueError(
                f"param_map[{name!r}]['out_of_range'] must be one of {OUT_OF_RANGE}, "
                f"got {out_of_range!r}"
            )
        if out_of_range == "clamp" and spec.get("choices") is not None:
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
            out_of_range=out_of_range,
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


def check_range(name: str, value: Any, spec: Mapping) -> Any:
    """Raise ``ValueError`` unless ``value`` fits ``spec``'s ``min``/``max``/``choices``.

    The standalone form of the translator's ``out_of_range='raise'`` check; returns
    ``value`` unchanged.
    """
    _range_problem_raise(name, value, _parse_spec(name, dict(spec)) or _Spec(name))
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


def _range_problem_raise(name: str, value: Any, spec: _Spec) -> None:
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

    Returns:
        ``translate``. Its optional ``on_unsupported=`` is the *caller's* policy for
        this one call; when given it replaces both the backend's policy and
        ``always_raise``.
    """
    _check_policy(on_unsupported)
    specs = {name: _parse_spec(name, spec) for name, spec in param_map.items()}
    supported = sorted(n for n, s in specs.items() if s is not None)
    raising = frozenset(always_raise)
    passing = frozenset(passthrough)
    vocab = dict(vocabulary) if vocabulary is not None else None
    where = backend or _DEFAULT_WHERE
    default_policy = on_unsupported

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
        if policy == "raise":
            changes_meaning = call_policy is None and name in raising
            detail = (
                ", and dropping it would change what you get"
                if changes_meaning
                else f". Supported: {supported}"
            )
            raise UnsupportedParameter(
                f"{name}={value!r} {reason or 'is ' + _kind(name) + ' ' + where}"
                f"{detail}. Remove it, pick a backend that supports it, or pass "
                "on_unsupported='note' to drop it with a note."
            )
        message = (
            f"{name}={value!r} {reason or 'is ' + _kind(name) + ' ' + where}; dropped"
        )
        if policy == "warn":
            warnings.warn(message, UserWarning, stacklevel=_WARN_STACKLEVEL)
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
                    _range_problem_raise(name, value, spec)
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
        f"{name}={value!r}{unit} is outside {where}'s [{spec.min}, {spec.max}]{unit} "
        f"window; clamped to {shown}{unit}"
    )
    return clamped
