"""The ledger: a data-driven gallery of OCR backends.

ocracy ships a *ledger* — a JSON catalog (``ocracy/data/backends.json``) that
describes **every** OCR engine/service we know about, whether or not ocracy
ships a working facade for it. Keeping this data *out of the code* is deliberate:
the catalog is curated research, it changes far more often than the code, and
users (and downstream tools) can read, filter, diff, and extend it without
touching Python.

This module reads that JSON and exposes it as a filterable, dict-like
:class:`Catalog` of :class:`BackendInfo` records::

    from ocracy import catalog

    catalog["tesseract"]                          # one backend's info
    catalog.filter(is_local=True, open_source=True)   # only local OSS engines
    catalog.filter(handwriting="yes")             # engines that read handwriting
    catalog.filter(implemented=True)              # only what ocracy can run today
    catalog.supports_language("fra")              # engines that list French
    catalog.to_dataframe()                        # pandas view (if installed)

Each record follows the schema documented in ``data/SCHEMA.md``. The special
``implemented`` flag is computed *live* from the backend registry, so it can
never drift from the code: a backend is "implemented" iff a real adapter exists
under :mod:`ocracy.backends`.

The loader itself is :mod:`ocracy.kit.ledger`, shared with the other fleet facades;
this module binds ocracy's data to it: the ledger path, the ``OCRACY_LEDGER``
override, the registry, and the OCR-specific fields.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from ocracy.kit.ledger import DEFAULT_TEXT_FIELDS, BackendInfo
from ocracy.kit.ledger import Catalog as _LedgerCatalog

__all__ = ["BackendInfo", "Catalog", "catalog", "DEFAULT_LEDGER_PATH"]

DEFAULT_LEDGER_PATH = Path(__file__).parent / "data" / "backends.json"
LEDGER_ENV_VAR = "OCRACY_LEDGER"

# Fields whose meaning is "membership in a free-text description", handled
# specially by :meth:`Catalog.filter` rather than by exact equality.
_TEXT_MEMBERSHIP_FIELDS = frozenset(DEFAULT_TEXT_FIELDS)

# ``can("math")`` also reads the ledger's ``math_formula`` field.
_CAPABILITY_SUFFIXES = ("_formula",)

_COMPARE_FIELDS = (
    "name",
    "is_local",
    "is_remote",
    "open_source",
    "pricing_model",
    "price_note",
    "accuracy_tier",
    "languages_count",
    "handwriting",
    "math_formula",
    "tables",
    "best_for",
)


def _implemented_ids() -> set:
    """Ids of backends with a real adapter, computed live from the registry."""
    try:
        from ocracy import registry

        return set(registry.list_backends())
    except Exception:
        return set()


class Catalog(_LedgerCatalog):
    """ocracy's ledger: :class:`ocracy.kit.ledger.Catalog` bound to ocracy's data.

    Loaded lazily from :data:`DEFAULT_LEDGER_PATH` (override via the ``path``
    argument or the ``OCRACY_LEDGER`` environment variable). :meth:`filter`
    returns a *new* ``Catalog`` over the matching subset, so filters compose::

        catalog.filter(is_remote=True).filter(pricing_model="free_tier_then_paid")
    """

    def __init__(
        self,
        path: Optional[Union[str, Path]] = None,
        *,
        _records: Optional[List[dict]] = None,
    ):
        super().__init__(
            path,
            records=_records,
            default_path=DEFAULT_LEDGER_PATH,
            env_var=LEDGER_ENV_VAR,
            implemented=_implemented_ids,
            text_fields=_TEXT_MEMBERSHIP_FIELDS,
            capability_suffixes=_CAPABILITY_SUFFIXES,
            compare_fields=_COMPARE_FIELDS,
        )


# Module-level singleton — the canonical ledger.
catalog = Catalog()
