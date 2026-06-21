"""Command-line tools for ocracy (dispatched via argh in ``__main__``).

Each function here is a thin, CLI-friendly wrapper over the Python API; ``argh``
turns their signatures into subcommands and options. Run ``ocracy <command>
--help`` (after ``pip install 'ocracy[cli]'``) or ``python -m ocracy <command>``.
"""

from __future__ import annotations

import json
from typing import Optional

import ocracy

__all__ = [
    "read",
    "backends",
    "info",
    "find",
    "scaffold",
    "validate",
    "requirements",
    "doctor",
    "install",
]


def _split_csv(value: Optional[str]):
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def read(
    image: str,
    *,
    backend: Optional[str] = None,
    languages: Optional[str] = None,
    output: str = "text",
):
    """OCR an image and print the result.

    :param image: Path or http(s) URL to the image.
    :param backend: Backend id (default: first installed). See ``ocracy backends``.
    :param languages: Comma-separated language codes, e.g. ``en,fr``.
    :param output: ``text`` (default), ``json`` (text + blocks), or ``markdown``.
    """
    kwargs = {}
    langs = _split_csv(languages)
    if langs:
        kwargs["languages"] = langs
    result = ocracy.ocr(image, backend=backend, **kwargs)

    if output == "json":
        return json.dumps(
            {
                "backend": result.backend,
                "text": result.text,
                "blocks": [
                    {
                        "text": b.text,
                        "level": b.level,
                        "confidence": b.confidence,
                        "bbox": b.bbox.as_tuple if b.bbox else None,
                    }
                    for b in result.blocks
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    if output == "markdown":
        return result.markdown or result.text
    return result.text


def backends(*, capability: Optional[str] = None):
    """List the backends ocracy can run right now (optionally by capability).

    :param capability: Filter to a capability, e.g. ``math``, ``tables``, ``handwriting``.
    """
    ids = ocracy.list_backends(capability)
    lines = []
    for bid in ids:
        info_ = ocracy.catalog[bid] if bid in ocracy.catalog else None
        where = (
            "+".join(
                w
                for w, on in (("local", info_.is_local), ("remote", info_.is_remote))
                if on
            )
            if info_
            else "?"
        )
        lines.append(f"{bid:16} [{where}]")
    return "\n".join(lines)


def info(backend_id: str):
    """Print a backend's full ledger record as JSON.

    :param backend_id: A ledger id, e.g. ``google-vision`` (see ``ocracy find``).
    """
    return json.dumps(
        ocracy.catalog[backend_id].to_dict(), indent=2, ensure_ascii=False, default=str
    )


def find(
    *,
    local: bool = False,
    remote: bool = False,
    free: bool = False,
    implemented: bool = False,
    handwriting: bool = False,
    math: bool = False,
    tables: bool = False,
    language: Optional[str] = None,
):
    """Filter the ledger and print matching backends (id, where, pricing, best-for).

    Flags compose (AND). Example: ``ocracy find --local --free --handwriting``.

    :param local: Keep only backends that run locally.
    :param remote: Keep only hosted/remote backends.
    :param free: Keep only free / open-source backends.
    :param implemented: Keep only backends ocracy can run today.
    :param handwriting: Keep only backends that read handwriting.
    :param math: Keep only backends that read math/formulas.
    :param tables: Keep only backends that extract tables.
    :param language: Keep only backends whose languages mention this name/code.
    """
    cat = ocracy.catalog
    if local:
        cat = cat.filter(is_local=True)
    if remote:
        cat = cat.filter(is_remote=True)
    if free:
        cat = cat.filter(open_source=True)
    if implemented:
        cat = cat.filter(implemented=True)
    if handwriting:
        cat = cat.can("handwriting")
    if math:
        cat = cat.can("math")
    if tables:
        cat = cat.can("tables")
    if language:
        cat = cat.supports_language(language)

    lines = []
    for bid in cat.ids:
        i = cat[bid]
        where = "+".join(
            w for w, on in (("local", i.is_local), ("remote", i.is_remote)) if on
        )
        flag = "✓" if i.implemented else " "
        lines.append(
            f"[{flag}] {bid:26} [{where:13}] {i._record.get('pricing_model', '')!s:20} {i._record.get('best_for', '') or ''}"[
                :160
            ]
        )
    header = f"{len(cat)} backend(s) ([✓] = implemented):"
    return header + "\n" + "\n".join(lines)


def scaffold(backend_id: str, *, dest: Optional[str] = None):
    """Generate a new backend package from its ledger entry.

    :param backend_id: The ledger id to scaffold (e.g. ``surya``).
    :param dest: Optional destination directory.
    """
    path = ocracy.scaffold_backend(backend_id, dest=dest)
    return f"Scaffolded backend at: {path}\nNext: fill param_map in config.py and implement adapter.py's _read."


def validate(backend_id: str):
    """Smoke-test a backend adapter end to end and print the report.

    :param backend_id: The backend id to validate (e.g. ``tesseract``).
    """
    return json.dumps(
        ocracy.validate_adapter(backend_id), indent=2, ensure_ascii=False, default=str
    )


def requirements(backend_id: str, *, gpu: bool = False):
    """Show what a backend needs to run (pip, system deps, GPU, weights, creds).

    :param backend_id: Backend id, e.g. ``paddleocr``.
    :param gpu: Include GPU-wheel guidance.
    """
    return ocracy.requirements(backend_id, gpu=gpu).instructions()


def doctor():
    """Report which backends are usable now, and how to install the rest."""
    rep = ocracy.doctor()
    lines = ["Available now:"]
    lines += [f"  ✓ {b}" for b in rep["available"]] or ["  (none)"]
    lines.append("Not installed:")
    for bid, hint in sorted(rep["missing"].items()):
        lines.append(f"  ✗ {bid:26} {hint}")
    return "\n".join(lines)


def install(backend_id: str, *, gpu: bool = False, yes: bool = False):
    """Plan (default) or run (``--yes``) the pip install for a backend.

    Without ``--yes`` it prints the plan and changes nothing. System deps and GPU
    wheels are surfaced, not run automatically.

    :param backend_id: Backend id to install, e.g. ``rapidocr``.
    :param gpu: Surface GPU-wheel guidance.
    :param yes: Actually run ``pip install`` (otherwise just print the plan).
    """
    res = ocracy.install(backend_id, gpu=gpu, yes=yes)
    if res.get("ran"):
        ok = res.get("available_after")
        if ok:
            return f"Installed — '{backend_id}' is ready. ✓"
        return (
            f"pip exit {res['returncode']}; '{backend_id}' still not importable.\n"
            + res["requirements"].instructions()
        )
    return res.get("message") or res["requirements"].instructions()


# SSOT list of CLI-dispatchable functions.
_dispatch_funcs = [
    read,
    backends,
    info,
    find,
    scaffold,
    validate,
    requirements,
    doctor,
    install,
]
