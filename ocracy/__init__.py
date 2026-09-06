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

# Two unrelated tuples are called ``LEVELS`` inside ocracy: OCR granularity
# (``ocracy.base``) and backend readiness (``ocracy.status``). At the package root
# the readiness one owns the bare name ``ocracy.LEVELS`` — that is what it has
# meant since the status module landed, and what ``ocracy status`` reads. Each
# also gets an unambiguous alias below (``GRANULARITY_LEVELS`` / ``STATUS_LEVELS``)
# so neither is shadowed and no reader has to guess which tuple they are holding.
from ocracy.base import (
    BBox,
    ImageInput,
    LEVELS as GRANULARITY_LEVELS,
    OcrResult,
    TextBlock,
)
from ocracy.catalog import BackendInfo, Catalog, catalog
from ocracy.registry import (
    get_config,
    get_default_backend,
    list_backends,
    register_backend,
)
from ocracy.services import ServiceCollection
from ocracy.make_backend import (
    BaseOcrAdapter,
    make_block,
    scaffold_backend,
    validate_adapter,
)
from ocracy.install import (
    Requirements,
    available_backends,
    check,
    doctor,
    install,
    requirements,
)
from ocracy.status import (
    LEVELS,
    LEVELS as STATUS_LEVELS,
    backend_ids,
    backend_info,
    is_set_up,
    is_tested,
    names_with_sites,
    status_table,
)

__all__ = [
    "ocr",
    "read_text",
    "services",
    "catalog",
    "find",
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

# Derive the version from installed package metadata (the pyproject SSOT, which CI
# auto-bumps) so __version__ never drifts from a hardcoded literal.
from importlib.metadata import PackageNotFoundError as _PNFE, version as _version

try:
    __version__ = _version("ocracy")
except _PNFE:  # running from a source tree without install metadata
    __version__ = "0.0.0+source"
del _version, _PNFE

#: Singleton service collection for per-backend access (``services.tesseract``).
services = ServiceCollection()


def ocr(image: ImageInput, *, backend: str = None, **kwargs) -> OcrResult:
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
    backend = backend or get_default_backend()
    return services[backend].read(image, **kwargs)


def read_text(image: ImageInput, *, backend: str = None, **kwargs) -> str:
    """Like :func:`ocr` but returns just the recognized text string."""
    return ocr(image, backend=backend, **kwargs).text


def find(**criteria) -> Catalog:
    """Filter the ledger; shorthand for :meth:`ocracy.catalog.Catalog.filter`.

    Example::

        ocracy.find(is_local=True, open_source=True, handwriting="yes")
        ocracy.find(implemented=True)        # only backends ocracy can run now
    """
    return catalog.filter(**criteria)
