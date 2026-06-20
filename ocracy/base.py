"""Core types and normalized result objects for ocracy.

OCR engines disagree wildly on what they return: Tesseract emits TSV rows of
words with pixel boxes and confidences; cloud APIs return nested JSON of
pages/blocks/paragraphs/words; VLM-based engines often return just a Markdown
string. ocracy normalizes all of that into a small, stable set of dataclasses so
that callers get the *same shape* regardless of which backend produced the text:

- :class:`OcrResult` — the full result of reading an image: a concatenated
  ``text`` (in reading order) plus a list of structured ``blocks`` carrying
  bounding boxes and confidences, plus the untouched ``raw`` backend output for
  power users who need engine-specific detail.
- :class:`TextBlock` — one recognized unit of text (word/line/paragraph/block)
  with an optional :class:`BBox` and ``confidence``.
- :class:`BBox` — an axis-aligned bounding box, with an optional ``polygon`` for
  rotated or quadrilateral regions (common in scene-text engines).

The input side is normalized too: every facade function accepts an
:data:`ImageInput` — a path, URL, ``bytes``, PIL image, or numpy array. Concrete
decoding happens lazily in :mod:`ocracy.util`, so importing ocracy never
requires Pillow or numpy.

The design goal is *progressive disclosure*: ``str(result)`` gives you the text,
``result.text`` is the same string, iterating the result yields its lines, and
``result.blocks`` / ``result.raw`` are there when you need structure.
"""

from __future__ import annotations

from collections.abc import Sequence as _SequenceABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, List, Optional, Tuple, Union

# ---------------------------------------------------------------------------
# Input type
# ---------------------------------------------------------------------------

# Image input accepted by all facade functions. The string forms cover both a
# filesystem path and an ``http(s)://`` URL; ``bytes`` is raw encoded image
# data; the PIL/numpy forms are quoted because they are decoded lazily in
# ``ocracy.util`` and must never be imported at module load time.
ImageInput = Union[str, Path, bytes, "PILImage", "NDArray"]  # noqa: F821

# Recognition granularity levels, coarse -> fine is the other way round; this is
# the canonical ordering used for sorting and filtering blocks.
LEVELS: Tuple[str, ...] = ("page", "block", "paragraph", "line", "word", "char")


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BBox:
    """An axis-aligned bounding box in pixel coordinates (origin = top-left).

    ``polygon`` optionally carries the original (possibly rotated) vertices as a
    sequence of ``(x, y)`` points; the axis-aligned ``x0/y0/x1/y1`` are always
    populated (derived from the polygon if a backend only gives one).
    """

    x0: float
    y0: float
    x1: float
    y1: float
    polygon: Optional[Tuple[Tuple[float, float], ...]] = None

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    @property
    def xywh(self) -> Tuple[float, float, float, float]:
        """``(x, y, width, height)`` — the convention many drawing libs expect."""
        return (self.x0, self.y0, self.width, self.height)

    @property
    def as_tuple(self) -> Tuple[float, float, float, float]:
        """``(x0, y0, x1, y1)`` — the convention PIL's ``crop`` expects."""
        return (self.x0, self.y0, self.x1, self.y1)

    @classmethod
    def from_xywh(cls, x: float, y: float, w: float, h: float) -> "BBox":
        return cls(x0=x, y0=y, x1=x + w, y1=y + h)

    @classmethod
    def from_polygon(cls, points: _SequenceABC) -> "BBox":
        """Build a box from polygon vertices ``[(x, y), ...]``.

        The axis-aligned extent is computed from the vertices and the original
        polygon is preserved for callers that care about rotation.
        """
        pts = tuple((float(px), float(py)) for px, py in points)
        if not pts:
            raise ValueError("from_polygon requires at least one point")
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return cls(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys), polygon=pts)


# ---------------------------------------------------------------------------
# Text units
# ---------------------------------------------------------------------------


@dataclass
class TextBlock:
    """One recognized unit of text.

    Attributes:
        text: The recognized string for this unit.
        bbox: Where it was found (pixel coordinates), if the backend reports it.
        confidence: Recognition confidence in ``[0, 1]`` (normalized by ocracy
            from whatever scale the backend used), if available.
        level: Granularity — one of :data:`LEVELS` ("word", "line", ...).
        language: Detected/declared language code for this unit, if any.
        meta: Backend-specific extras (font size, style, page index, ...).
    """

    text: str
    bbox: Optional[BBox] = None
    confidence: Optional[float] = None
    level: str = "line"
    language: Optional[str] = None
    meta: dict = field(default_factory=dict)

    def __str__(self) -> str:
        return self.text


# ---------------------------------------------------------------------------
# The normalized result
# ---------------------------------------------------------------------------


@dataclass
class OcrResult:
    """The normalized result of reading an image with any backend.

    ``text`` is the headline payload: the full recognized text in reading order.
    ``blocks`` carries the structured units (with boxes/confidences) when the
    backend provides them. ``raw`` is the untouched backend output. ``meta``
    holds cross-cutting extras (languages, page count, a Markdown rendering,
    timing, ...).

    Progressive disclosure::

        result = ocracy.ocr("scan.png")
        print(result)              # -> the text
        result.text                # -> the same string
        for line in result:        # -> iterate TextBlocks (lines by default)
            print(line.text, line.confidence)
        result.words               # -> only word-level blocks
        result.mean_confidence     # -> average confidence, if available
        result.raw                 # -> engine-specific structure
    """

    text: str
    blocks: List[TextBlock] = field(default_factory=list)
    backend: str = ""
    raw: Any = None
    meta: dict = field(default_factory=dict)

    # -- string / iteration sugar ------------------------------------------
    def __str__(self) -> str:
        return self.text

    def __len__(self) -> int:
        return len(self.text)

    def __iter__(self) -> Iterator[TextBlock]:
        return iter(self.blocks)

    def __bool__(self) -> bool:
        return bool(self.text.strip()) or bool(self.blocks)

    # -- structured views ---------------------------------------------------
    def at_level(self, level: str) -> List[TextBlock]:
        """Blocks at a given granularity (``"word"``, ``"line"``, ...)."""
        return [b for b in self.blocks if b.level == level]

    @property
    def words(self) -> List[TextBlock]:
        return self.at_level("word")

    @property
    def lines(self) -> List[TextBlock]:
        return self.at_level("line")

    @property
    def paragraphs(self) -> List[TextBlock]:
        return self.at_level("paragraph")

    @property
    def mean_confidence(self) -> Optional[float]:
        """Mean confidence over blocks that report one, or ``None``."""
        confs = [b.confidence for b in self.blocks if b.confidence is not None]
        return sum(confs) / len(confs) if confs else None

    @property
    def markdown(self) -> Optional[str]:
        """Markdown rendering if the backend produced one (else ``None``)."""
        return self.meta.get("markdown")

    def filter_confidence(self, min_confidence: float) -> "OcrResult":
        """Return a copy keeping only blocks at or above ``min_confidence``.

        Blocks without a confidence are dropped. ``text`` is rebuilt from the
        surviving blocks (joined by newline).
        """
        kept = [
            b
            for b in self.blocks
            if b.confidence is not None and b.confidence >= min_confidence
        ]
        return OcrResult(
            text="\n".join(b.text for b in kept),
            blocks=kept,
            backend=self.backend,
            raw=self.raw,
            meta=dict(self.meta),
        )

    # -- constructors -------------------------------------------------------
    @classmethod
    def from_text(
        cls, text: str, *, backend: str = "", raw: Any = None, **meta: Any
    ) -> "OcrResult":
        """Build a minimal result from just a text string (no geometry)."""
        return cls(text=text, backend=backend, raw=raw, meta=meta)

    @classmethod
    def from_blocks(
        cls,
        blocks: List[TextBlock],
        *,
        backend: str = "",
        raw: Any = None,
        text: Optional[str] = None,
        joiner: str = "\n",
        **meta: Any,
    ) -> "OcrResult":
        """Build a result from structured blocks.

        If ``text`` is not given it is synthesized by joining the blocks' text in
        their given order with ``joiner`` (callers should pass blocks already in
        reading order, or pre-join and pass ``text`` explicitly).
        """
        if text is None:
            text = joiner.join(b.text for b in blocks)
        return cls(text=text, blocks=list(blocks), backend=backend, raw=raw, meta=meta)
