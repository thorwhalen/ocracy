"""The ledger loader: a filterable catalog over a facade's ``backends.json``.

Each fleet facade ships a *ledger*: a JSON catalog that describes every engine or
service in its domain, whether or not the facade can run it yet. The research
changes far more often than the code, so it is data, not code. This module reads
any such file and exposes it as a dict-like :class:`Catalog` of
:class:`BackendInfo` records. A facade binds its own data::

    from ocracy.kit.ledger import Catalog

    catalog = Catalog(
        default_path=Path(__file__).parent / "data" / "backends.json",
        env_var="ACME_LEDGER",                      # override the path from the env
        implemented=lambda: registry.list_backends(),
        text_fields=DEFAULT_TEXT_FIELDS | {"pros", "cons"},
    )
    catalog["some-engine"]                           # one record
    catalog.filter(is_local=True, open_source=True)  # a new Catalog; filters compose
    catalog.filter(implemented=True)                 # what the facade runs today
    catalog.supports_language("French")
    catalog.can("diarization")

``implemented`` is the one computed field. It comes from the facade's registry
through the ``implemented=`` callable, so it cannot drift from the code. A record
that stores its own ``implemented`` keeps it.

The seams, all keyword-only: ``default_path`` and ``env_var`` (where the JSON
lives), ``implemented`` (ids with a working adapter), ``text_fields`` (fields
filtered by case-insensitive membership rather than equality),
``capability_suffixes`` (extra field names :meth:`Catalog.can` looks at, such as
ocracy's ``math`` -> ``math_formula``) and ``compare_fields`` (the default columns
of :meth:`Catalog.compare`).

Stdlib only; imports nothing else from ocracy. pandas is imported by
:meth:`Catalog.to_dataframe` only.
"""

from __future__ import annotations

import copy
import importlib
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Union

__all__ = [
    "BackendInfo",
    "Catalog",
    "DEFAULT_TEXT_FIELDS",
    "DEFAULT_COMPARE_FIELDS",
    "CAPABILITY_VALUES",
]

#: Fields whose meaning is "membership in a free-text description": filtered by a
#: case-insensitive substring test rather than by equality.
DEFAULT_TEXT_FIELDS = frozenset({"languages_note", "beyond_text", "output_formats"})

#: The columns :meth:`Catalog.compare` shows when a facade does not name its own.
DEFAULT_COMPARE_FIELDS = (
    "name",
    "is_local",
    "is_remote",
    "open_source",
    "pricing_model",
    "price_note",
    "accuracy_tier",
    "languages_count",
    "best_for",
)

#: Field values that mean "this backend has the capability", for :meth:`Catalog.can`.
#: Compared by identity for ``True``, so a count of ``1`` is not a capability.
CAPABILITY_VALUES = ("yes", True)


def _has_value(value: Any) -> bool:
    return any(
        value is v if isinstance(v, bool) else value == v for v in CAPABILITY_VALUES
    )


_SHOWN_UNKNOWN_IDS = 20


class BackendInfo(Mapping):
    """One backend's ledger entry: a read-only record, by key or by attribute.

    New fields added to the JSON are available at once (``info.price_note``,
    ``info["price_note"]``) with no code change; a few common fields get typed
    properties.
    """

    def __init__(self, record: dict, *, implemented: bool = False):
        self._record: Dict[str, Any] = dict(record)
        self._record.setdefault("implemented", implemented)

    def __getitem__(self, key: str) -> Any:
        return self._record[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._record)

    def __len__(self) -> int:
        return len(self._record)

    def __getattr__(self, name: str) -> Any:
        # Only called when normal attribute lookup fails.
        try:
            return self._record[name]
        except KeyError:
            raise AttributeError(name)

    @property
    def id(self) -> str:
        return self._record.get("id", "")

    @property
    def name(self) -> str:
        return self._record.get("name", self.id)

    @property
    def is_local(self) -> bool:
        return bool(self._record.get("is_local", False))

    @property
    def is_remote(self) -> bool:
        return bool(self._record.get("is_remote", False))

    @property
    def implemented(self) -> bool:
        return bool(self._record.get("implemented", False))

    def to_dict(self) -> dict:
        return dict(self._record)

    def __repr__(self) -> str:
        where = (
            "+".join(
                w
                for w, on in (("local", self.is_local), ("remote", self.is_remote))
                if on
            )
            or "?"
        )
        impl = "implemented" if self.implemented else "listed"
        return f"<BackendInfo {self.id!r} [{where}] {impl}>"


def _matches(info: BackendInfo, field: str, wanted: Any, text_fields) -> bool:
    """Whether the criterion ``field=wanted`` holds for ``info``.

    Equality by default; a case-insensitive membership test for ``text_fields``.
    A ``wanted`` that is a set/list/tuple means "one of these".
    """
    value = info._record.get(field)
    if field in text_fields:
        hay = value if isinstance(value, str) else " ".join(map(str, value or []))
        needles = wanted if isinstance(wanted, (set, list, tuple)) else [wanted]
        return any(str(n).lower() in hay.lower() for n in needles)
    if isinstance(wanted, (set, list, tuple)):
        return value in wanted
    return value == wanted


def _nothing_implemented() -> Iterable[str]:
    return ()


class Catalog(Mapping):
    """A filterable, dict-like collection of :class:`BackendInfo`, keyed by id.

    Loaded lazily from ``path``, else from the ``env_var`` environment variable,
    else from ``default_path``; a missing file is an empty catalog. ``records``
    gives the records directly instead. :meth:`filter` returns a new ``Catalog``
    with the same settings over the matching subset, so filters compose::

        catalog.filter(is_remote=True).filter(pricing_model="free_tier_then_paid")

    Args:
        path: The ledger JSON (a ``{"backends": [...]}`` object or a bare list).
        records: The records themselves, instead of a file.
        default_path: Where the ledger lives when neither ``path`` nor the
            environment says otherwise.
        env_var: An environment variable that overrides ``default_path``.
        implemented: Returns the ids that have a working adapter; called once,
            on first load.
        text_fields: Fields filtered by case-insensitive membership.
        capability_suffixes: Field-name suffixes :meth:`can` also checks:
            ``("", "_formula")`` makes ``can("math")`` read ``math_formula``.
        compare_fields: Default columns of :meth:`compare`.
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        *,
        records: Optional[List[dict]] = None,
        default_path: Optional[Union[str, Path]] = None,
        env_var: Optional[str] = None,
        implemented: Callable[[], Iterable[str]] = _nothing_implemented,
        text_fields: Iterable[str] = DEFAULT_TEXT_FIELDS,
        capability_suffixes: Iterable[str] = ("",),
        compare_fields: Iterable[str] = DEFAULT_COMPARE_FIELDS,
    ):
        self._path = Path(path) if path else None
        self._explicit_records = records
        self._default_path = Path(default_path) if default_path else None
        self._env_var = env_var
        self._implemented = implemented
        self._text_fields = frozenset(text_fields)
        self._capability_suffixes = tuple(capability_suffixes)
        self._compare_fields = tuple(compare_fields)
        self._cache: Optional[Dict[str, BackendInfo]] = None

    # -- loading ------------------------------------------------------------
    def _resolve_path(self) -> Optional[Path]:
        if self._path is not None:
            return self._path
        env = os.environ.get(self._env_var) if self._env_var else None
        return Path(env) if env else self._default_path

    def _read_records(self) -> List[dict]:
        if self._explicit_records is not None:
            return self._explicit_records
        path = self._resolve_path()
        if path is None or not path.exists():
            return []
        import json  # here, not at the top: importing the kit stays cheap

        data = json.loads(path.read_text(encoding="utf-8"))
        return data["backends"] if isinstance(data, dict) else data

    def _load(self) -> Dict[str, BackendInfo]:
        if self._cache is None:
            records = self._read_records()
            implemented_ids = set(self._implemented())
            self._cache = {
                r["id"]: BackendInfo(r, implemented=r["id"] in implemented_ids)
                for r in records
            }
        return self._cache

    def _subset(self, records: List[dict]) -> "Catalog":
        """A catalog with this one's settings over ``records``."""
        subset = copy.copy(self)
        subset._path = None
        subset._explicit_records = records
        subset._cache = None
        return subset

    # -- Mapping interface --------------------------------------------------
    def __getitem__(self, key: str) -> BackendInfo:
        try:
            return self._load()[key]
        except KeyError:
            raise KeyError(
                f"Unknown backend id: {key!r}. "
                f"Known ids: {sorted(self._load().keys())[:_SHOWN_UNKNOWN_IDS]}..."
            )

    def __iter__(self) -> Iterator[str]:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())

    # -- filtering / querying ----------------------------------------------
    def filter(
        self,
        *,
        predicate: Optional[Callable[[BackendInfo], bool]] = None,
        implemented: Optional[bool] = None,
        **criteria: Any,
    ) -> "Catalog":
        """Return a new ``Catalog`` of backends matching every criterion.

        Args:
            predicate: An arbitrary ``BackendInfo -> bool`` callable.
            implemented: If set, keep only (un)implemented backends.
            **criteria: ``field=value`` constraints. ``value`` may be a
                set/list/tuple meaning "one of". The catalog's text fields (by
                default ``languages_note``, ``beyond_text``, ``output_formats``)
                use a case-insensitive substring match.

        Example::

            catalog.filter(is_local=True, open_source=True)
        """
        text_fields = self._text_fields

        def keep(info: BackendInfo) -> bool:
            if implemented is not None and info.implemented is not implemented:
                return False
            if predicate is not None and not predicate(info):
                return False
            return all(_matches(info, f, v, text_fields) for f, v in criteria.items())

        return self._subset([i.to_dict() for i in self._load().values() if keep(i)])

    def supports_language(self, language: str) -> "Catalog":
        """Backends whose ``languages_note`` mentions ``language`` (name or code)."""
        return self.filter(languages_note=language)

    def can(self, capability: str) -> "Catalog":
        """Backends with ``capability``: listed in ``beyond_text``, or a field set.

        A field counts when it is named ``capability`` plus one of the catalog's
        ``capability_suffixes`` and its value is one of :data:`CAPABILITY_VALUES`.
        """
        names = [capability + suffix for suffix in self._capability_suffixes]

        def has(info: BackendInfo) -> bool:
            record = info._record
            return capability in (record.get("beyond_text") or []) or any(
                _has_value(record.get(n)) for n in names
            )

        return self.filter(predicate=has)

    # -- export -------------------------------------------------------------
    @property
    def ids(self) -> List[str]:
        return sorted(self._load().keys())

    def to_records(self) -> List[dict]:
        return [i.to_dict() for i in self._load().values()]

    def to_dataframe(self, *, columns: Optional[Iterable[str]] = None):
        """Return a pandas DataFrame of the catalog (pandas imported lazily)."""
        try:
            pd = importlib.import_module("pandas")
        except ImportError as e:
            raise ImportError(
                "to_dataframe() requires 'pandas'. Install it with: "
                f"pip install pandas\nOriginal error: {e}"
            ) from e
        df = pd.DataFrame(self.to_records())
        if columns is not None:
            df = df[list(columns)]
        return df

    def compare(
        self,
        ids: Optional[Iterable[str]] = None,
        *,
        fields: Optional[Iterable[str]] = None,
    ) -> List[dict]:
        """A trimmed, side-by-side view of selected backends and fields."""
        chosen = list(ids) if ids is not None else self.ids
        fields = list(fields) if fields is not None else list(self._compare_fields)
        out = []
        for i in chosen:
            info = self[i]
            row = {"id": info.id}
            row.update({f: info._record.get(f) for f in fields})
            out.append(row)
        return out

    def __repr__(self) -> str:
        records = self._load()
        n_impl = sum(1 for i in records.values() if i.implemented)
        n_local = sum(1 for i in records.values() if i.is_local)
        n_remote = sum(1 for i in records.values() if i.is_remote)
        return (
            f"<Catalog {len(records)} backends | {n_impl} implemented | "
            f"{n_local} local, {n_remote} remote>"
        )
