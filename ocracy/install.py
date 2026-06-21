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

import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional

__all__ = [
    "Requirements",
    "requirements",
    "check",
    "available_backends",
    "doctor",
    "install",
]


def _platform() -> str:
    p = sys.platform
    if p.startswith("darwin"):
        return "darwin"
    if p.startswith("linux"):
        return "linux"
    if p.startswith("win"):
        return "windows"
    return p


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


@dataclass
class Requirements:
    """What a backend needs to run — structured for an agent to act on."""

    backend_id: str
    implemented: bool
    available: bool  # importable / usable right now
    is_local: bool
    is_remote: bool
    pip_command: str  # the line to run
    extra: Optional[str] = None
    system: List[str] = field(default_factory=list)  # OS-specific shell commands
    system_note: Optional[str] = None
    gpu: Optional[str] = None
    weights: Optional[str] = None
    heavy: bool = False
    alternative: Optional[str] = None
    credentials: List[str] = field(default_factory=list)  # "ENV_VAR — where to get it"
    notes: List[str] = field(default_factory=list)

    def instructions(self) -> str:
        """An agent-/human-readable, copy-pasteable install plan."""
        if self.available:
            return f"'{self.backend_id}' is already installed and usable. ✓"
        lines = [f"To use the '{self.backend_id}' backend:"]
        n = 1
        if self.system:
            lines.append(f"  {n}. System dependency:")
            for cmd in self.system:
                lines.append(f"       {cmd}")
            if self.system_note:
                lines.append(f"     ({self.system_note})")
            n += 1
        lines.append(f"  {n}. {self.pip_command}")
        if self.gpu:
            lines.append(f"       GPU: {self.gpu}")
        n += 1
        if self.credentials:
            lines.append(f"  {n}. Set credential(s):")
            for c in self.credentials:
                lines.append(f"       {c}")
            n += 1
        if self.weights:
            lines.append(f"  • {self.weights}")
        if self.heavy:
            lines.append(
                "  • Note: large download (deep-learning framework + weights)."
            )
        if self.alternative:
            lines.append(f"  • Lighter alternative: {self.alternative}.")
        for note in self.notes:
            lines.append(f"  • {note}")
        lines.append(
            f"Verify:   python -c \"import ocracy; print(ocracy.check('{self.backend_id}'))\""
        )
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.instructions()


def _credential_lines(env_var_field: str, provider: str) -> List[str]:
    if not env_var_field:
        return []
    from ocracy.credentials import CREDENTIAL_GUIDANCE

    g = CREDENTIAL_GUIDANCE.get(provider)
    link = f"  (get a key: {g['get_key_url']})" if g else ""
    return [f"export {env_var_field}{link}"]


def requirements(backend_id: str, *, gpu: bool = False) -> Requirements:
    """Return structured install :class:`Requirements` for ``backend_id``.

    Works for both implemented backends (uses the ``ocracy[extra]`` install and
    the recipe) and ledger-only backends (falls back to the ledger's
    ``python_install`` string). Pass ``gpu=True`` to surface GPU wheel guidance.
    """
    from ocracy import registry
    from ocracy.catalog import catalog

    implemented = backend_id in set(registry.list_backends())
    recipe = _RECIPES.get(backend_id, {})
    record = catalog[backend_id].to_dict() if backend_id in catalog else {}
    cfg = registry.get_config(backend_id) if implemented else {}

    is_local = bool(cfg.get("is_local", record.get("is_local", False)))
    is_remote = bool(cfg.get("is_remote", record.get("is_remote", False)))
    available = check(backend_id) if implemented else False

    # pip command: prefer the ocracy extra for implemented backends, else the
    # ledger's python_install string.
    extra = recipe.get("extra") or (backend_id if implemented else None)
    if implemented and extra:
        pip_command = f'pip install "ocracy[{extra}]"'
    else:
        ledger_pip = (record.get("python_install") or "").strip()
        pip_command = ledger_pip or f'pip install "ocracy[{backend_id}]"'

    system = list(recipe.get("system", {}).get(_platform(), []))
    api_env = cfg.get("api_env_var") or record.get("api_env_var") or ""
    credentials = (
        _credential_lines(api_env, backend_id) if is_remote and api_env else []
    )

    notes = list(recipe.get("notes", []))
    if not implemented:
        notes.append(
            f"ocracy does not yet ship a facade for '{backend_id}' — it's in the ledger "
            "only. See the ocracy-add-backend skill to wrap it."
        )

    return Requirements(
        backend_id=backend_id,
        implemented=implemented,
        available=available,
        is_local=is_local,
        is_remote=is_remote,
        pip_command=pip_command,
        extra=extra,
        system=system,
        system_note=recipe.get("system_note"),
        gpu=recipe.get("gpu") if (gpu or recipe.get("gpu")) else None,
        weights=recipe.get("weights"),
        heavy=bool(recipe.get("heavy")),
        alternative=recipe.get("alt"),
        credentials=credentials,
        notes=notes,
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
    result = {
        "backend": backend_id,
        "requirements": req,
        "ran": False,
        "available_before": req.available,
    }
    if req.available:
        result["message"] = f"'{backend_id}' is already available — nothing to do."
        return result
    if not req.implemented:
        result["message"] = req.instructions()
        return result
    if not yes:
        result["message"] = (
            "Dry run — pass yes=True to run the pip install.\n" + req.instructions()
        )
        return result

    import subprocess

    target = f"ocracy[{req.extra}]" if req.extra else backend_id
    cmd = [sys.executable, "-m", "pip", "install"]
    if upgrade:
        cmd.append("--upgrade")
    cmd.append(target)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result["ran"] = True
    result["pip_argv"] = cmd
    result["returncode"] = proc.returncode
    result["stdout_tail"] = proc.stdout[-2000:]
    result["stderr_tail"] = proc.stderr[-2000:]
    if verify and proc.returncode == 0:
        # Importability is module-cached; probe in a fresh interpreter.
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import ocracy; print(ocracy.check('{backend_id}'))",
            ],
            capture_output=True,
            text=True,
        )
        result["available_after"] = probe.stdout.strip() == "True"
    if req.system:
        result["system_todo"] = req.system
    return result
