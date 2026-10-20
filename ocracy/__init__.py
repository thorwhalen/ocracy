"""ocracy — one facade over many OCR engines, plus a ledger to choose between them.

OCR ("read the text in this image") is solved a dozen different ways: local
engines (Tesseract, EasyOCR, PaddleOCR), cloud APIs (Google Vision, AWS
Textract, Azure), and VLM-based readers — each with its own install, API,
pricing, language coverage, and quirks. ocracy gives you:

1. **A uniform facade.** Call :func:`ocr` and get the same :class:`~ocracy.base.OcrResult`
   back no matter which backend ran::

       import ocracy
       result = ocracy.ocr("scan.png")          # default (first installed) backend
       print(result)                            # -> the recognized text
       result = ocracy.ocr("scan.png", backend="easyocr", languages=["en", "fr"])

   Convenience: :func:`read_text` returns just the string.

2. **A ledger / gallery** of *every* engine we researched — not only the ones
   with a working facade — so you can choose with eyes open::

       ocracy.catalog                                   # the whole ledger
       ocracy.find(is_local=True, open_source=True)     # filter it
       ocracy.find(handwriting="yes", is_remote=True)
       ocracy.catalog.to_dataframe()                    # browse as a table

   The ledger lives in data (``ocracy/data/backends.json``), not code.

3. **Tools to build new facades.** The catalog is large; ocracy ships a facade
   for a curated subset and gives you the machinery (and a SKILL) to add any
   other one in minutes::

       from ocracy.make_backend import scaffold_backend, validate_adapter
       scaffold_backend("mathpix")    # generate a backend package from the ledger
       validate_adapter("tesseract")  # smoke-test an adapter end to end

Three tiers of access, from simplest to most powerful::

    ocracy.ocr(img)                                # facade, default backend
    ocracy.services.tesseract.read(img, lang="fra")  # pick a backend
    ocracy.services.tesseract.adapter              # raw engine adapter
"""

import sys as _sys
import types as _types
from typing import TYPE_CHECKING

# Two unrelated tuples are called ``LEVELS`` inside ocracy: OCR granularity
# (``ocracy.base``) and backend readiness (``ocracy.status``). At the package root
# the readiness one owns the bare name ``ocracy.LEVELS`` — that is what it has
# meant since the status module landed, and what ``ocracy status`` reads. Each
# also gets an unambiguous alias below (``GRANULARITY_LEVELS`` / ``STATUS_LEVELS``)
# so neither is shadowed and no reader has to guess which tuple they are holding.
#
# The root re-exports are LAZY (PEP 562, issue #11): every facade that imports
# ``ocracy.kit`` runs this file first, and the kit uses none of them. Each name
# below maps to ``(module, attribute)`` and is imported on first access, then
# cached in this module's globals. ``TYPE_CHECKING`` keeps them visible to type
# checkers and IDEs.
_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    "BBox": ("ocracy.base", "BBox"),
    "ImageInput": ("ocracy.base", "ImageInput"),
    "GRANULARITY_LEVELS": ("ocracy.base", "LEVELS"),
    "OcrResult": ("ocracy.base", "OcrResult"),
    "TextBlock": ("ocracy.base", "TextBlock"),
    "BackendInfo": ("ocracy.catalog", "BackendInfo"),
    "Catalog": ("ocracy.catalog", "Catalog"),
    "catalog": ("ocracy.catalog", "catalog"),
    "benchmark": ("ocracy.benchmark", "benchmark"),
    "get_config": ("ocracy.registry", "get_config"),
    "get_default_backend": ("ocracy.registry", "get_default_backend"),
    "list_backends": ("ocracy.registry", "list_backends"),
    "register_backend": ("ocracy.registry", "register_backend"),
    "ServiceCollection": ("ocracy.services", "ServiceCollection"),
    "services": ("ocracy.services", "services"),
    "BaseOcrAdapter": ("ocracy.make_backend", "BaseOcrAdapter"),
    "make_block": ("ocracy.make_backend", "make_block"),
    "scaffold_backend": ("ocracy.make_backend", "scaffold_backend"),
    "validate_adapter": ("ocracy.make_backend", "validate_adapter"),
    "Requirements": ("ocracy.install", "Requirements"),
    "available_backends": ("ocracy.install", "available_backends"),
    "check": ("ocracy.install", "check"),
    "doctor": ("ocracy.install", "doctor"),
    "install": ("ocracy.install", "install"),
    "requirements": ("ocracy.install", "requirements"),
    "LEVELS": ("ocracy.status", "LEVELS"),
    "STATUS_LEVELS": ("ocracy.status", "LEVELS"),
    "backend_ids": ("ocracy.status", "backend_ids"),
    "backend_info": ("ocracy.status", "backend_info"),
    "is_set_up": ("ocracy.status", "is_set_up"),
    "is_tested": ("ocracy.status", "is_tested"),
    "names_with_sites": ("ocracy.status", "names_with_sites"),
    "status_table": ("ocracy.status", "status_table"),
}

#: Root names that are ALSO the names of submodules (``ocracy.catalog`` the
#: module vs ``ocracy.catalog`` the ledger instance, and likewise ``install``
#: and ``services``). Eagerly, the ``from ... import`` ran after the submodule
#: import and so won. Lazily, importing the submodule later would make the
#: import system bind the MODULE over the root name; :class:`_Root` refuses
#: exactly that binding, so the root export keeps winning.
_SUBMODULE_SHADOWED = frozenset({"benchmark", "catalog", "install", "services"})

if TYPE_CHECKING:  # pragma: no cover - static view of the lazy names
    from ocracy.base import LEVELS as GRANULARITY_LEVELS
    from ocracy.base import BBox, ImageInput, OcrResult, TextBlock
    from ocracy.benchmark import benchmark
    from ocracy.catalog import BackendInfo, Catalog, catalog
    from ocracy.install import (
        Requirements,
        available_backends,
        check,
        doctor,
        install,
        requirements,
    )
    from ocracy.make_backend import (
        BaseOcrAdapter,
        make_block,
        scaffold_backend,
        validate_adapter,
    )
    from ocracy.registry import (
        get_config,
        get_default_backend,
        list_backends,
        register_backend,
    )
    from ocracy.services import ServiceCollection
    from ocracy.status import LEVELS
    from ocracy.status import LEVELS as STATUS_LEVELS
    from ocracy.status import (
        backend_ids,
        backend_info,
        is_set_up,
        is_tested,
        names_with_sites,
        status_table,
    )

    services: ServiceCollection

__all__ = [
    "ocr",
    "read_text",
    "services",
    "catalog",
    "find",
    "benchmark",
    "list_backends",
    "register_backend",
    "get_default_backend",
    "get_config",
    "OcrResult",
    "TextBlock",
    "BBox",
    "ImageInput",
    "GRANULARITY_LEVELS",
    "BackendInfo",
    "Catalog",
    "ServiceCollection",
    "BaseOcrAdapter",
    "make_block",
    "scaffold_backend",
    "validate_adapter",
    "requirements",
    "check",
    "doctor",
    "install",
    "available_backends",
    "Requirements",
    "backend_ids",
    "backend_info",
    "status_table",
    "names_with_sites",
    "is_set_up",
    "is_tested",
    "LEVELS",
    "STATUS_LEVELS",
    "__version__",
]


def __getattr__(name: str):
    """Resolve a lazy root name on first access (PEP 562), then cache it.

    - ``__version__`` comes from installed package metadata (the pyproject SSOT,
      which CI auto-bumps), not a hardcoded literal. An editable install's
      metadata is frozen at install time, so there it can lag ``pyproject.toml``
      until a reinstall.
    - Every other re-export comes from :data:`_LAZY_EXPORTS`, including the
      ``services`` singleton, which ``ocracy.services`` creates at its import so
      the import lock keeps it unique across threads.
    - A submodule (``ocracy.status``) is imported, as the eager re-exports used
      to do as a side effect. So ``hasattr(ocracy, name)`` may import
      ``ocracy.<name>``, and a submodule that fails to import raises rather than
      answering ``False``.

    Nothing here runs on ``import ocracy`` or ``import ocracy.kit``.
    """
    import importlib

    if name == "__version__":
        from importlib.metadata import PackageNotFoundError, version

        try:
            value = version("ocracy")
        except PackageNotFoundError:  # a source tree without install metadata
            value = "0.0.0+source"
    elif name in _LAZY_EXPORTS:
        module_name, attr = _LAZY_EXPORTS[name]
        value = getattr(importlib.import_module(module_name), attr)
    else:
        try:
            return importlib.import_module(f"{__name__}.{name}")
        except ModuleNotFoundError as exc:
            if exc.name != f"{__name__}.{name}":
                raise
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    globals()[name] = value
    return value


def __dir__():
    """List the lazy names too, before their first access."""
    return sorted(set(globals()) | set(__all__))


class _Root(_types.ModuleType):
    """The package's module type: refuses to let a submodule shadow a root export.

    It drops any binding of ``ocracy.catalog`` / ``.install`` / ``.services`` to
    the same-named submodule, including an explicit one
    (``ocracy.catalog = sys.modules["ocracy.catalog"]`` is silently ignored).
    ``type(ocracy)`` is this class, so ``isinstance(ocracy, ModuleType)`` holds
    but ``type(ocracy) is ModuleType`` does not.
    """

    def __setattr__(self, name, value):
        if (
            name in _SUBMODULE_SHADOWED
            and isinstance(value, _types.ModuleType)
            and value.__name__ == f"{__name__}.{name}"
        ):
            return  # the import system binding ocracy.<name>; the root export wins
        super().__setattr__(name, value)


_sys.modules[__name__].__class__ = _Root


def ocr(image: "ImageInput", *, backend: str = None, **kwargs) -> "OcrResult":
    """Read text from an image with any backend, returning a normalized result.

    Args:
        image: A path, ``http(s)`` URL, ``bytes``, PIL image, or numpy array.
        backend: Backend id (see :func:`list_backends`). Defaults to the first
            *installed* implemented backend (see :func:`get_default_backend`).
        **kwargs: Normalized, backend-translated options (e.g. ``languages``).
            Unknown options for the chosen backend are warned about and dropped.

    Returns:
        An :class:`~ocracy.base.OcrResult` (``str(result)`` is the text).
    """
    from ocracy import get_default_backend, services

    backend = backend or get_default_backend()
    return services[backend].read(image, **kwargs)


def read_text(image: "ImageInput", *, backend: str = None, **kwargs) -> str:
    """Like :func:`ocr` but returns just the recognized text string."""
    return ocr(image, backend=backend, **kwargs).text


def find(**criteria) -> "Catalog":
    """Filter the ledger; shorthand for :meth:`ocracy.catalog.Catalog.filter`.

    Example::

        ocracy.find(is_local=True, open_source=True, handwriting="yes")
        ocracy.find(implemented=True)        # only backends ocracy can run now
    """
    from ocracy import catalog

    return catalog.filter(**criteria)
