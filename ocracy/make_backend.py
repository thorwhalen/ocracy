"""Abstraction tools for *building* OCR facades.

Writing a new backend should be mostly declarative. This module supplies the
reusable machinery so an adapter is just "call the engine, return normalized
blocks":

- :class:`BaseOcrAdapter` — subclass it and implement :meth:`~BaseOcrAdapter._read`;
  kwarg translation (via the backend's ``param_map``) is handled for you.
- :func:`make_block` / :func:`as_bbox` — build normalized :class:`~ocracy.base.TextBlock`
  / :class:`~ocracy.base.BBox` from whatever shape the engine returned, including
  confidence-scale normalization (e.g. Tesseract's ``0..100`` -> ``0..1``).
- :func:`scaffold_backend` — generate a new ``ocracy/backends/<id>/`` package from
  the template, pre-filled from the ledger entry. This is the one-command way to
  start a facade for any backend in the catalog.
- :func:`make_test_image` / :func:`validate_adapter` — smoke-test an adapter end
  to end so you know a new facade actually works.

These are the "abstraction tools and skills that know the process" — the
companion :file:`SKILL.md` walks an agent (or human) through using them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Union

from ocracy.base import BBox, OcrResult, TextBlock
from ocracy.translation import make_kwargs_translator

__all__ = [
    "BaseOcrAdapter",
    "make_block",
    "as_bbox",
    "normalize_confidence",
    "scaffold_backend",
    "make_test_image",
    "validate_adapter",
]

_TEMPLATE_DIR = Path(__file__).parent / "backends" / "_template"


# ---------------------------------------------------------------------------
# Adapter base class
# ---------------------------------------------------------------------------


class BaseOcrAdapter:
    """Optional base class for backend adapters.

    Stores the config, builds a kwarg translator from ``config['param_map']``,
    and implements ``read`` as: translate normalized kwargs -> native kwargs ->
    :meth:`_read`. Subclasses implement :meth:`_read` and return an
    :class:`~ocracy.base.OcrResult`.

    Adapters are not *required* to subclass this — the registry only needs an
    ``Adapter`` class with a ``read(image, **kwargs)`` method — but doing so
    removes the boilerplate.
    """

    def __init__(self, config: dict):
        self.config = config
        self.backend_id = config.get("id") or config.get("name", "")
        param_map = config.get("param_map")
        self._translate = make_kwargs_translator(param_map) if param_map else None

    def read(self, image, **kwargs) -> OcrResult:
        native = self._translate(**kwargs) if self._translate else dict(kwargs)
        return self._read(image, **native)

    def _read(self, image, **native_kwargs) -> OcrResult:  # pragma: no cover
        raise NotImplementedError(
            f"{type(self).__name__}._read is not implemented for "
            f"backend {self.backend_id!r}."
        )


# ---------------------------------------------------------------------------
# Result-building helpers
# ---------------------------------------------------------------------------


def normalize_confidence(
    value: Optional[float], *, scale: float = 1.0
) -> Optional[float]:
    """Normalize a raw confidence to ``[0, 1]`` (dividing by ``scale``).

    ``None`` passes through. Use ``scale=100`` for engines that report ``0..100``.
    """
    if value is None:
        return None
    v = float(value) / scale if scale and scale != 1.0 else float(value)
    return max(0.0, min(1.0, v))


def as_bbox(obj: Any) -> Optional[BBox]:
    """Coerce common bbox shapes into a :class:`~ocracy.base.BBox`.

    Accepts a ``BBox`` (returned as-is), a 4-tuple ``(x0, y0, x1, y1)``, or a
    polygon ``[(x, y), ...]`` (4+ points). ``None`` passes through.
    """
    if obj is None or isinstance(obj, BBox):
        return obj
    seq = list(obj)
    if len(seq) == 4 and all(isinstance(v, (int, float)) for v in seq):
        return BBox(float(seq[0]), float(seq[1]), float(seq[2]), float(seq[3]))
    return BBox.from_polygon(seq)


def make_block(
    text: str,
    *,
    bbox: Any = None,
    confidence: Optional[float] = None,
    conf_scale: float = 1.0,
    level: str = "word",
    language: Optional[str] = None,
    **meta: Any,
) -> TextBlock:
    """Build a normalized :class:`~ocracy.base.TextBlock`.

    ``bbox`` may be any shape accepted by :func:`as_bbox`. ``confidence`` is
    normalized to ``[0, 1]`` via ``conf_scale`` (e.g. ``conf_scale=100`` for
    percent-scale engines).
    """
    return TextBlock(
        text=text,
        bbox=as_bbox(bbox),
        confidence=normalize_confidence(confidence, scale=conf_scale),
        level=level,
        language=language,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Scaffolding a new backend from the ledger
# ---------------------------------------------------------------------------

_TEMPLATE_LINE = re.compile(
    # A config line tagged for scaffold rewriting. Trailing text after the
    # ``# TEMPLATE`` marker (a usage hint) is allowed and ignored.
    r'^(?P<indent>\s*)"(?P<key>\w+)":\s*(?P<val>.*?),\s*#\s*TEMPLATE\b.*$'
)


def _fmt_value(v: Any) -> str:
    # Booleans first (bool is a subclass of int and of json's number handling).
    if isinstance(v, bool):
        return "True" if v else "False"
    if v is None:
        return '""'
    # json.dumps emits a correctly-escaped, Python-compatible literal — crucial
    # for strings that contain quotes/backslashes (e.g. a description mentioning
    # a "sandwich" PDF), which naive f-string quoting would turn into invalid code.
    return json.dumps(v, ensure_ascii=False)


def _overrides_from_record(backend_id: str, record: Optional[dict]) -> dict:
    """Map a ledger record onto the template's ``# TEMPLATE`` config keys."""
    record = record or {}
    pip_install = (record.get("python_install") or "").strip()
    pip_install = re.sub(r"^\s*pip\s+install\s+", "", pip_install).strip()
    desc = (
        record.get("best_for")
        or (record.get("pros") or [None])[0]
        or record.get("name")
        or backend_id
    )
    return {
        "id": backend_id,
        "name": backend_id,
        "display_name": record.get("name") or record.get("display_name") or backend_id,
        "pip_install": pip_install or "PACKAGE",
        "import_name": backend_id.replace("-", "_"),
        "license": record.get("license") or "unknown",
        "is_local": bool(record.get("is_local", False)),
        "is_remote": bool(record.get("is_remote", False)),
        "description": desc,
    }


def _render_config(template_text: str, overrides: dict) -> str:
    out_lines = []
    for line in template_text.splitlines():
        m = _TEMPLATE_LINE.match(line)
        if m and m.group("key") in overrides:
            key = m.group("key")
            out_lines.append(
                f'{m.group("indent")}"{key}": {_fmt_value(overrides[key])},'
            )
        else:
            out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if template_text.endswith("\n") else "")


def scaffold_backend(
    backend_id: str,
    *,
    dest: Optional[Union[str, Path]] = None,
    overwrite: bool = False,
    ledger: Any = None,
    extra_overrides: Optional[dict] = None,
) -> Path:
    """Create a new ``ocracy/backends/<id>/`` package from the template.

    Pre-fills ``config.py`` from the backend's ledger entry (if any) so you only
    have to flesh out ``param_map`` and implement ``adapter.py``'s ``_read``.

    Args:
        backend_id: The ledger id (e.g. ``"easyocr"``, ``"google-vision"``). The
            on-disk module name uses underscores; the config ``id`` keeps the id
            verbatim.
        dest: Target directory (defaults to ``ocracy/backends/<id_underscored>``).
        overwrite: Allow writing into an existing non-empty directory.
        ledger: A :class:`~ocracy.catalog.Catalog` to read the record from
            (defaults to the shipped catalog).
        extra_overrides: Extra config-key overrides applied on top of the record.

    Returns:
        The path to the created backend package.
    """
    record = None
    try:
        if ledger is None:
            from ocracy.catalog import catalog as ledger
        if backend_id in ledger:
            record = ledger[backend_id].to_dict()
    except Exception:
        record = None

    overrides = _overrides_from_record(backend_id, record)
    if extra_overrides:
        overrides.update(extra_overrides)

    module_name = backend_id.replace("-", "_")
    dest = Path(dest) if dest else (_TEMPLATE_DIR.parent / module_name)
    if dest.exists() and any(dest.iterdir()) and not overwrite:
        raise FileExistsError(
            f"{dest} already exists and is not empty (pass overwrite=True)."
        )
    dest.mkdir(parents=True, exist_ok=True)

    config_text = _render_config(
        (_TEMPLATE_DIR / "config.py").read_text(encoding="utf-8"), overrides
    )
    adapter_text = (_TEMPLATE_DIR / "adapter.py").read_text(encoding="utf-8")
    init_text = (
        f'"""{overrides["display_name"]} backend for ocracy."""\n'
    )

    (dest / "__init__.py").write_text(init_text, encoding="utf-8")
    (dest / "config.py").write_text(config_text, encoding="utf-8")
    (dest / "adapter.py").write_text(adapter_text, encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def make_test_image(text: str = "OCR test 123", *, size=(640, 140), font_size: int = 48):
    """Render a black-on-white test image with ``text`` (needs Pillow).

    Uses a real TrueType font (DejaVuSans, then Pillow's sized default) at a
    legible size so OCR engines can actually read it — important for
    :func:`validate_adapter` to be a meaningful smoke test.
    """
    from ocracy.util import check_import

    pil_image = check_import("PIL.Image", install_hint="Pillow", feature="make_test_image")
    pil_draw = check_import("PIL.ImageDraw", install_hint="Pillow", feature="make_test_image")

    font = None
    try:
        from PIL import ImageFont

        try:
            font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        except OSError:
            # Pillow >= 10.1 supports a size argument to the bundled default font.
            font = ImageFont.load_default(font_size)
    except Exception:  # noqa: BLE001 - fall back to the unsized default
        font = None

    img = pil_image.new("RGB", size, "white")
    draw = pil_draw.Draw(img)
    draw.text((20, 40), text, fill="black", font=font)
    return img


def validate_adapter(
    backend_id: str, *, image: Any = None, expect_text: Optional[str] = None
) -> dict:
    """Smoke-test a backend adapter end to end, returning a report dict.

    Loads the adapter (reporting unavailability instead of raising), runs
    ``read`` on a generated (or supplied) image, and checks the contract: an
    :class:`~ocracy.base.OcrResult` came back with text and/or blocks. Never
    raises on a *recognition* mismatch — it returns what happened so callers can
    decide.
    """
    from ocracy import registry

    report: dict = {"backend": backend_id, "available": False, "ran": False, "ok": False}

    try:
        registry.get_config(backend_id)
    except KeyError as e:
        report["error"] = f"not registered: {e}"
        return report

    try:
        adapter = registry.get_backend(backend_id)["adapter"]
    except ImportError as e:
        report["error"] = f"adapter import failed: {e}"
        return report

    # Adapters import their engine lazily, so the class loads even without it.
    # "Available" must reflect whether the engine dependency is actually present.
    report["available"] = registry._is_available(backend_id)
    if not report["available"]:
        cfg = registry.get_config(backend_id)
        report["error"] = (
            f"engine not importable ({cfg.get('import_name')}); "
            f"install with: pip install {cfg.get('pip_install', backend_id)}"
        )
        return report

    if image is None:
        try:
            image = make_test_image()
        except ImportError as e:
            report["error"] = f"cannot generate test image: {e}"
            return report

    try:
        result = adapter.read(image)
        report["ran"] = True
    except Exception as e:  # noqa: BLE001 - report any runtime error
        report["error"] = f"{type(e).__name__}: {e}"
        return report

    report["returns_ocrresult"] = isinstance(result, OcrResult)
    report["text"] = getattr(result, "text", None)
    report["n_blocks"] = len(getattr(result, "blocks", []) or [])
    report["mean_confidence"] = getattr(result, "mean_confidence", None)
    report["has_bbox"] = any(b.bbox is not None for b in getattr(result, "blocks", []))
    text_ok = bool((report["text"] or "").strip()) or report["n_blocks"] > 0
    if expect_text is not None:
        text_ok = expect_text.lower() in (report["text"] or "").lower()
    report["ok"] = bool(report["returns_ocrresult"] and text_ok)
    return report
