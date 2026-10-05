"""Install helpers — make it easy (for a human *or* an AI agent) to get a backend running.

Many backends are not just ``pip install`` away: Tesseract needs a *system*
binary, PaddleOCR pulls a deep-learning framework (with separate CPU/GPU wheels),
Torch-based engines (EasyOCR, TrOCR, pix2tex) are heavy and download model weights
on first use, and the remote backends need a credential rather than a package.

This module turns those realities into structured, OS-aware guidance an agent can
act on:

- :func:`requirements` — what a backend needs (pip extra, system deps for *this*
  OS, GPU notes, model-weight notes, credential env vars), plus whether it's
  already importable. ``Requirements.instructions()`` renders an agent-/human-
  readable plan.
- :func:`check` / :func:`doctor` — is a backend (or every backend) usable right now?
- :func:`install` — optionally run the ``pip install`` for a backend (with
  confirmation) and verify it. System deps and GPU wheels are *surfaced*, not run
  automatically (they need sudo/brew or environment-specific CUDA choices).

The companion ``ocracy-install-backend`` skill walks an agent through using these.
"""

from __future__ import annotations

from typing import Dict, List

from ocracy.kit.install import Requirements, build_requirements, run_install

__all__ = [
    "Requirements",
    "requirements",
    "check",
    "available_backends",
    "doctor",
    "install",
]

_PACKAGE = "ocracy"


# ---------------------------------------------------------------------------
# Per-backend install recipes (the tricky knowledge, in one place)
#
# Only fields that differ from the trivial "pip install ocracy[<id>]" need an
# entry. ``extra`` is the pyproject extra name when it differs from the backend id.
# ``system`` maps platform -> shell commands. ``gpu`` is an alternative/extra pip
# line for GPU. ``weights`` notes first-run model downloads. ``alt`` suggests a
# lighter backend with comparable results.
# ---------------------------------------------------------------------------
_RECIPES: Dict[str, dict] = {
    "tesseract": {
        "extra": "tesseract",
        "system": {
            "darwin": ["brew install tesseract"],
            "linux": ["sudo apt-get update && sudo apt-get install -y tesseract-ocr"],
            "windows": [
                "Install the UB-Mannheim Tesseract build: "
                "https://github.com/UB-Mannheim/tesseract/wiki  (or: choco install tesseract)"
            ],
        },
        "system_note": "Tesseract needs the system 'tesseract' binary (the pip package is only a wrapper).",
        "notes": [
            "Extra languages: 'brew install tesseract-lang' (macOS) or "
            "'apt-get install tesseract-ocr-<lang>' (Linux), e.g. tesseract-ocr-fra."
        ],
    },
    "easyocr": {
        "extra": "easyocr",
        "heavy": True,
        "gpu": "For GPU, install a CUDA build of torch first (see https://pytorch.org/get-started/locally/).",
        "weights": "Downloads recognition/detection model weights on first use (cached under ~/.EasyOCR).",
        "alt": "rapidocr (same PP-OCR-class accuracy, much lighter install, no Torch)",
    },
    "rapidocr": {
        "extra": "rapidocr",
        "weights": "Model weights ship inside the wheel — no first-run download.",
        "notes": [
            "Light, CPU-only (ONNXRuntime); the recommended default for local plain-text OCR.",
            "Runs the same PP-OCR models as paddleocr. For tables/layout/formula "
            "(PP-Structure), the larger server models, GPU-scale throughput, or "
            "fine-tuning, use paddleocr instead.",
        ],
    },
    "paddleocr": {
        "extra": "paddleocr",
        "heavy": True,
        "gpu": "For GPU, replace paddlepaddle with the CUDA build: pip install paddlepaddle-gpu "
        "(match your CUDA version per https://www.paddlepaddle.org.cn/en/install/quick).",
        "weights": "Downloads PP-OCR model weights on first use (cached under ~/.paddleocr).",
        "alt": "rapidocr — the same PP-OCR text models via ONNX, lighter and CPU-only "
        "(plain-text recognition only)",
        "notes": [
            "For plain printed text, prefer rapidocr (lighter, same models). Choose "
            "paddleocr when you want the larger server models, GPU throughput, "
            "fine-tuning, or to grow into PP-Structure (tables/layout/formula) / "
            "PaddleOCR-VL — capabilities RapidOCR does not provide.",
            "PaddlePaddle wheels are platform/Python-version sensitive; if the install "
            "fights you and you only need plain text, switch to rapidocr.",
        ],
    },
    "ocrmac": {
        "extra": "ocrmac",
        "system_note": "macOS only — uses the built-in Apple Vision framework (no extra system install).",
        "notes": ["Not available on Linux/Windows."],
    },
    "pix2tex-latex-ocr": {
        "extra": "pix2tex",
        "heavy": True,
        "gpu": "GPU optional; install a CUDA torch build for speed (https://pytorch.org/get-started/locally/).",
        "weights": "Downloads the LaTeX-OCR model on first use.",
    },
    "trocr-handwritten": {
        "extra": "trocr",
        "heavy": True,
        "gpu": "GPU optional; install a CUDA torch build for speed (https://pytorch.org/get-started/locally/).",
        "weights": "Downloads the TrOCR checkpoint from Hugging Face on first use (~1.3 GB for base).",
    },
    # Remote backends — the 'install' is mostly a small client + a credential.
    "ocr-space": {"extra": "ocr-space"},
    "google-vision": {"extra": "google-vision"},
    "aws-textract": {"extra": "aws-textract"},
    "azure-document-intelligence": {"extra": "azure"},
    "mistral-ocr": {"extra": "mistral"},
    "mathpix": {"extra": "mathpix"},
    "claude-vision": {"extra": "anthropic"},
    "gpt-4o-vision": {"extra": "openai"},
}


def _verify_code(backend_id: str) -> str:
    return f"import ocracy; print(ocracy.check('{backend_id}'))"


def requirements(backend_id: str, *, gpu: bool = False) -> Requirements:
    """Return structured install :class:`Requirements` for ``backend_id``.

    Works for both implemented backends (uses the ``ocracy[extra]`` install and
    the recipe) and ledger-only backends (falls back to the ledger's
    ``python_install`` string). A recipe's GPU guidance is always included;
    ``gpu`` is accepted for compatibility and changes nothing.
    """
    from ocracy import registry
    from ocracy.catalog import catalog
    from ocracy.credentials import CREDENTIAL_GUIDANCE
    from ocracy.kit.credentials import credential_lines

    implemented = backend_id in set(registry.list_backends())
    record = catalog[backend_id].to_dict() if backend_id in catalog else {}
    cfg = registry.get_config(backend_id) if implemented else {}

    is_local = bool(cfg.get("is_local", record.get("is_local", False)))
    is_remote = bool(cfg.get("is_remote", record.get("is_remote", False)))
    api_env = cfg.get("api_env_var") or record.get("api_env_var") or ""
    credentials = (
        credential_lines(api_env, backend_id, guidance=CREDENTIAL_GUIDANCE)
        if is_remote and api_env
        else []
    )
    return build_requirements(
        backend_id,
        package=_PACKAGE,
        implemented=implemented,
        available=check(backend_id) if implemented else False,
        recipe=_RECIPES.get(backend_id),
        is_local=is_local,
        is_remote=is_remote,
        ledger_pip=record.get("python_install") or "",
        credentials=credentials,
        verify_command=f'python -c "{_verify_code(backend_id)}"',
        unimplemented_note=(
            f"ocracy does not yet ship a facade for '{backend_id}' — it's in the ledger "
            "only. See the ocracy-add-backend skill to wrap it."
        ),
    )


def check(backend_id: str) -> bool:
    """Is ``backend_id`` importable / usable right now? (no install, no network)."""
    from ocracy import registry

    return registry._is_available(backend_id)


def available_backends() -> List[str]:
    """Implemented backends whose dependency is importable right now."""
    from ocracy import registry

    return [b for b in registry.list_backends() if registry._is_available(b)]


def doctor() -> dict:
    """Report which implemented backends are usable now and what the rest need.

    Returns ``{"available": [...], "missing": {id: one-line install hint}}``.
    """
    from ocracy import registry

    available, missing = [], {}
    for bid in registry.list_backends():
        if registry._is_available(bid):
            available.append(bid)
        else:
            req = requirements(bid)
            hint = req.pip_command
            if req.system:
                hint = f"{req.system[0]} ; {hint}"
            missing[bid] = hint
    return {"available": available, "missing": missing}


def install(
    backend_id: str,
    *,
    yes: bool = False,
    gpu: bool = False,
    verify: bool = True,
    upgrade: bool = False,
) -> dict:
    """Plan (and optionally run) the pip install for a backend.

    With ``yes=False`` (default) this is a **dry run**: it returns the plan
    without changing anything — call ``result['requirements'].instructions()`` to
    show it. With ``yes=True`` it runs ``pip install`` for the backend's extra in
    the current interpreter, then (if ``verify``) checks importability.

    System dependencies and GPU wheels are *surfaced*, never run automatically
    (they need sudo/brew or an environment-specific CUDA choice) — run those
    yourself from ``result['requirements'].system`` / ``.gpu``.
    """
    req = requirements(backend_id, gpu=gpu)
    return run_install(
        req,
        package=_PACKAGE,
        yes=yes,
        verify_code=_verify_code(backend_id) if verify else None,
        upgrade=upgrade,
    )
