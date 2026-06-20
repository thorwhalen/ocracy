"""Image-input normalization and small shared helpers.

Different OCR backends want their input in different forms: a filesystem path
(Tesseract, PaddleOCR), raw ``bytes`` (most cloud REST APIs), a PIL image, or a
numpy array (deep-learning engines). Callers, meanwhile, want to pass whatever
they have — a path, an ``http(s)`` URL, bytes, a PIL image, or an array. This
module bridges the two with a handful of converters that **lazily** import
Pillow / numpy / urllib only when actually exercised, so ``import ocracy`` stays
dependency-free.

The key converters:

- :func:`load_image_bytes` — anything -> encoded image ``bytes`` (for REST APIs).
- :func:`ensure_file_path` — anything -> a path on disk (writing a temp file for
  in-memory inputs); pair with :func:`cleanup_temp` or use :func:`image_path`.
- :func:`image_path` — a context manager yielding a path and cleaning up.
- :func:`to_pil` / :func:`to_numpy` — anything -> a PIL image / numpy array.
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import Iterator, Optional, Tuple

from ocracy.base import ImageInput

__all__ = [
    "classify_input",
    "is_url",
    "load_image_bytes",
    "ensure_file_path",
    "cleanup_temp",
    "image_path",
    "to_pil",
    "to_numpy",
    "check_import",
]


def check_import(module_name: str, *, install_hint: str, feature: str = "this"):
    """Import ``module_name`` or raise a friendly, actionable ImportError.

    Centralizes the "you need to ``pip install X``" guidance so adapters and
    converters don't each hand-roll it.
    """
    try:
        import importlib

        return importlib.import_module(module_name)
    except ImportError as e:  # pragma: no cover - exercised via adapters
        raise ImportError(
            f"{feature} requires {module_name!r}. Install it with: "
            f"pip install {install_hint}\nOriginal error: {e}"
        ) from e


def is_url(x: object) -> bool:
    """True if ``x`` is a string that looks like an http(s) URL."""
    return isinstance(x, str) and x.lower().startswith(("http://", "https://"))


def classify_input(image: ImageInput) -> str:
    """Classify an image input as ``url``/``path``/``bytes``/``pil``/``numpy``.

    Decided structurally (and via duck typing for PIL/numpy) so we never import
    Pillow or numpy just to look at the input.
    """
    if isinstance(image, (bytes, bytearray)):
        return "bytes"
    if is_url(image):
        return "url"
    if isinstance(image, (str, Path)):
        return "path"
    # Duck-type without importing the libs.
    if image.__class__.__module__.startswith("PIL"):
        return "pil"
    if image.__class__.__module__.startswith("numpy") or hasattr(image, "__array__"):
        return "numpy"
    raise TypeError(
        f"Unsupported image input of type {type(image).__name__}. Expected a path, "
        "URL, bytes, PIL.Image, or numpy.ndarray."
    )


def _fetch_url(url: str, *, timeout: float = 30.0) -> bytes:
    from urllib.request import urlopen  # stdlib, no extra dependency

    with urlopen(url, timeout=timeout) as resp:  # noqa: S310 - user-supplied URL
        return resp.read()


def to_pil(image: ImageInput):
    """Convert any supported input into a PIL ``Image`` (lazy import)."""
    # ``PIL.Image`` is the module exposing ``open`` / ``fromarray``.
    pil_image = check_import("PIL.Image", install_hint="Pillow", feature="image decoding")
    kind = classify_input(image)
    if kind == "pil":
        return image
    if kind == "numpy":
        return pil_image.fromarray(image)
    if kind == "bytes":
        import io

        return pil_image.open(io.BytesIO(bytes(image)))
    if kind == "url":
        import io

        return pil_image.open(io.BytesIO(_fetch_url(image)))
    # path
    return pil_image.open(os.fspath(image))


def to_numpy(image: ImageInput):
    """Convert any supported input into a numpy array (lazy import)."""
    np = check_import("numpy", install_hint="numpy", feature="array conversion")
    kind = classify_input(image)
    if kind == "numpy":
        return image
    return np.asarray(to_pil(image))


def load_image_bytes(image: ImageInput, *, fmt: str = "PNG") -> bytes:
    """Return encoded image ``bytes`` for any supported input.

    Pass-through for ``bytes``; reads files; fetches URLs; encodes PIL/numpy
    inputs as ``fmt`` (PNG by default — lossless and universally accepted).
    """
    kind = classify_input(image)
    if kind == "bytes":
        return bytes(image)
    if kind == "path":
        return Path(os.fspath(image)).read_bytes()
    if kind == "url":
        return _fetch_url(image)
    # pil / numpy -> encode in-memory
    import io

    pil = to_pil(image)
    buf = io.BytesIO()
    pil.save(buf, format=fmt)
    return buf.getvalue()


def ensure_file_path(
    image: ImageInput, *, suffix: str = ".png"
) -> Tuple[str, bool]:
    """Return ``(path, is_temp)`` for any supported input.

    Existing on-disk paths are returned untouched (``is_temp=False``). In-memory
    inputs (bytes/URL/PIL/numpy) are written to a temp file (``is_temp=True``);
    the caller is responsible for cleanup (use :func:`cleanup_temp`, or prefer
    the :func:`image_path` context manager).
    """
    if classify_input(image) == "path":
        return os.fspath(image), False
    data = load_image_bytes(image, fmt=suffix.lstrip(".").upper().replace("JPG", "JPEG"))
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="ocracy_")
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    return path, True


def cleanup_temp(path: str, is_temp: bool) -> None:
    """Delete ``path`` iff ``is_temp`` (the flag returned by :func:`ensure_file_path`)."""
    if is_temp:
        with contextlib.suppress(OSError):
            os.remove(path)


@contextlib.contextmanager
def image_path(image: ImageInput, *, suffix: str = ".png") -> Iterator[str]:
    """Context manager yielding a filesystem path for ``image``, cleaning up temps.

    Example::

        with image_path(pil_image) as p:
            text = pytesseract.image_to_string(p)
    """
    path, is_temp = ensure_file_path(image, suffix=suffix)
    try:
        yield path
    finally:
        cleanup_temp(path, is_temp)
