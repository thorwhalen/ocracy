"""Score OCR backends on a labelled corpus: how well does each read *your* documents?

::

    import ocracy
    rows = ocracy.benchmark("my_scans/")             # my_scans/truth.json: {"a.png": "text", ...}
    rows = ocracy.benchmark({"a.png": "Hello world"}, backends=["tesseract", "easyocr"])
    from ocracy.benchmark import summary
    print(summary(rows))                             # mean CER / WER / seconds per backend

A **corpus** is a mapping from image to reference text: a plain ``dict`` (or any ``dol``
store / ``Mapping``), or a folder holding a ``truth.json`` of ``{file name: text}``.
:func:`benchmark` returns one row (a ``dict``) per (backend, image) with the backend id,
the image, the scores, ``seconds``, the ``error`` if the backend raised (the run goes on)
and the ``hypothesis`` text.

Three seams, all keyword arguments:

* ``metric`` - a ``(reference, hypothesis) -> float`` callable, or a ``{column: callable}``
  mapping. The default is stdlib-only :data:`DFLT_METRICS` (``cer`` and ``wer``), so
  ``import ocracy`` stays dependency-free; hand it ``ek.metrics`` functions for others.
* ``read`` - the function that runs one backend, ``(image, *, backend, **kw) -> OcrResult``;
  defaults to :func:`ocracy.ocr`. Swap it to benchmark anything else, or to test offline.
* ``normalize`` - applied to reference and hypothesis before scoring (default: collapse
  whitespace, so line-break differences do not count as errors).

Note: at the package root ``ocracy.benchmark`` is the function (as ``ocracy.catalog`` is the
ledger), so reach this module's other names with ``from ocracy.benchmark import summary``,
not ``import ocracy.benchmark as m``.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path

__all__ = [
    "benchmark",
    "summary",
    "load_corpus",
    "cer",
    "wer",
    "edit_distance",
    "DFLT_METRICS",
    "TRUTH_FILE",
]

#: Name of the reference file looked up in a corpus folder.
TRUTH_FILE = "truth.json"

Metric = Callable[[str, str], float]


def edit_distance(a: Sequence, b: Sequence) -> int:
    """Levenshtein distance between two sequences (characters, words, ...).

    >>> edit_distance("kitten", "sitting")
    3
    >>> edit_distance(["a", "b"], ["a"])
    1
    """
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(
                min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y))
            )
        previous = current
    return previous[-1]


def _error_rate(reference: Sequence, hypothesis: Sequence) -> float:
    if not reference:
        return 0.0 if not hypothesis else 1.0
    return edit_distance(reference, hypothesis) / len(reference)


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate: edit distance over the reference length (0 is perfect).

    >>> cer("hello", "hallo")
    0.2
    >>> cer("", "")
    0.0
    """
    return _error_rate(reference, hypothesis)


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate: like :func:`cer`, over whitespace-separated words.

    >>> wer("the cat sat", "the cat")
    0.3333333333333333
    """
    return _error_rate(reference.split(), hypothesis.split())


DFLT_METRICS: Mapping[str, Metric] = {"cer": cer, "wer": wer}


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def load_corpus(corpus) -> dict:
    """The corpus as ``{image: reference text}``.

    ``corpus`` is a ``Mapping`` (kept as is), or a folder with a :data:`TRUTH_FILE`
    (``{file name: text}``; names are resolved against the folder), or the path to such
    a JSON file (names resolved against its folder).

    >>> load_corpus({"a.png": "x"})
    {'a.png': 'x'}
    """
    if isinstance(corpus, Mapping):
        return dict(corpus)
    path = Path(corpus).expanduser()
    truth = path / TRUTH_FILE if path.is_dir() else path
    if not truth.is_file():
        raise FileNotFoundError(
            f"No corpus at {path}: expected a mapping, a folder holding "
            f"{TRUTH_FILE}, or a JSON file of {{image: reference text}}."
        )
    folder = truth.parent
    data = json.loads(truth.read_text(encoding="utf-8"))
    return {str(folder / name): text for name, text in data.items()}


def _as_metrics(metric) -> Mapping[str, Metric]:
    if metric is None:
        return DFLT_METRICS
    if callable(metric):
        return {"score": metric}
    return metric


def _split_backends(backends) -> list[str]:
    if backends is None:
        from ocracy.install import available_backends

        return available_backends()
    if isinstance(backends, str):
        return [b.strip() for b in backends.split(",") if b.strip()]
    return list(backends)


def benchmark(
    corpus,
    backends: Iterable[str] | str | None = None,
    *,
    metric: Metric | Mapping[str, Metric] | None = None,
    read: Callable | None = None,
    normalize: Callable[[str], str] = _collapse_whitespace,
    **read_kwargs,
) -> list[dict]:
    """Run each backend over each image of ``corpus`` and score what it read.

    Args:
        corpus: ``{image: reference text}``, or a folder with a ``truth.json``
            (see :func:`load_corpus`).
        backends: Backend ids (list, or comma-separated string). Default: every
            implemented backend that is installed right now.
        metric: A ``(reference, hypothesis) -> float`` callable (column ``score``) or a
            ``{column: callable}`` mapping. Default: :data:`DFLT_METRICS` (``cer``, ``wer``).
        read: ``(image, *, backend, **read_kwargs) -> OcrResult``; default :func:`ocracy.ocr`.
        normalize: Applied to reference and hypothesis before scoring.
        **read_kwargs: Passed to every read, e.g. ``languages=["en"]``.

    Returns:
        One dict per (backend, image): ``backend``, ``image``, one key per metric,
        ``seconds``, ``error`` (``None`` unless the backend raised) and ``hypothesis``.
        A failed read has ``None`` scores; it never stops the run.

    >>> fake = lambda image, *, backend, **kw: type("R", (), {"text": "helo"})()
    >>> rows = benchmark({"a.png": "hello"}, ["x"], read=fake)
    >>> rows[0]["backend"], rows[0]["cer"], rows[0]["error"]
    ('x', 0.2, None)
    """
    if read is None:
        from ocracy import ocr as read
    metrics = _as_metrics(metric)
    references = load_corpus(corpus)
    if not references:
        raise ValueError("The corpus is empty: nothing to benchmark.")
    backend_ids = _split_backends(backends)
    if not backend_ids:
        raise ValueError(
            "No backends to run: none is installed. Pass backends=[...] or see `ocracy doctor`."
        )
    rows = []
    for backend in backend_ids:
        for image, reference in references.items():
            row = {"backend": backend, "image": image, **dict.fromkeys(metrics)}
            start = time.perf_counter()
            try:
                hypothesis = read(image, backend=backend, **read_kwargs).text or ""
                seconds = time.perf_counter() - start
                ref, hyp = normalize(reference), normalize(hypothesis)
                scores = {name: fn(ref, hyp) for name, fn in metrics.items()}
            except Exception as e:  # one bad backend/image/metric must not sink the run
                row.update(
                    seconds=time.perf_counter() - start,
                    error=f"{type(e).__name__}: {e}",
                    hypothesis=None,
                )
            else:
                row.update(scores, seconds=seconds, error=None, hypothesis=hypothesis)
            rows.append(row)
    return rows


def summary(rows: Iterable[Mapping]) -> str:
    """A text table: per backend, the mean of every score and of ``seconds`` over the images
    it read successfully, then ``ok/failed`` image counts. Columns come from the first row.
    """
    rows = list(rows)
    skip = {"backend", "image", "error", "hypothesis", "seconds"}
    columns = [k for k in (rows[0] if rows else {}) if k not in skip]
    lines = [
        "  ".join(
            [
                f"{'backend':<28}",
                *(f"{c:>8}" for c in columns),
                f"{'seconds':>8}",
                "ok/failed",
            ]
        )
    ]
    for backend in dict.fromkeys(r["backend"] for r in rows):
        mine = [r for r in rows if r["backend"] == backend]
        good = [r for r in mine if r["error"] is None]

        def mean(key):
            return (
                f"{sum(r[key] for r in good) / len(good):8.3f}" if good else f"{'-':>8}"
            )

        lines.append(
            "  ".join(
                [
                    f"{backend:<28}",
                    *(mean(c) for c in columns),
                    mean("seconds"),
                    f"{len(good)}/{len(mine) - len(good)}",
                ]
            )
        )
    return "\n".join(lines)
