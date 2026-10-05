"""Install plans: what a backend needs on *this* OS, as data an agent can act on.

Many backends are not one ``pip install`` away: a system binary (``brew install
tesseract``), a GPU wheel, first-run model weights, a credential. A package keeps
that knowledge as a ``recipes`` table (backend id -> recipe) and this module turns
one recipe into a :class:`Requirements` whose :meth:`~Requirements.instructions` is a
copy-pasteable plan::

    >>> req = build_requirements(
    ...     "tess", package="ocracy", implemented=True, available=False,
    ...     recipe={"system": {"linux": ["apt-get install tesseract-ocr"]}},
    ...     platform="linux",
    ... )
    >>> req.pip_command
    'pip install "ocracy[tess]"'
    >>> req.system
    ['apt-get install tesseract-ocr']

A recipe needs only the fields that differ from the trivial
``pip install "<package>[<id>]"``: ``extra`` (the pyproject extra, when it differs
from the id), ``system`` (platform -> shell commands), ``system_note``, ``gpu`` (an
alternative pip line), ``weights`` (first-run downloads), ``heavy``, ``alt`` (a
lighter backend) and ``notes``.

:func:`run_install` executes the pip part of a plan (``yes=True`` only) and verifies
it in a fresh interpreter. System commands and GPU wheels are surfaced, never run:
they need sudo, brew, or a CUDA choice only the user can make.

The registry and ledger lookups stay in the package (they are the package's
knowledge); :mod:`ocracy.install` is the worked example. Stdlib only; imports
nothing else from ocracy.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Iterable, List, Mapping, Optional

__all__ = [
    "Requirements",
    "current_platform",
    "build_requirements",
    "run_install",
]

#: How much of pip's stdout/stderr an install result keeps.
OUTPUT_TAIL_CHARS = 2000

_PLATFORM_PREFIXES = (("darwin", "darwin"), ("linux", "linux"), ("win", "windows"))


def current_platform() -> str:
    """``'darwin'``, ``'linux'``, ``'windows'``, or ``sys.platform`` for anything else."""
    for prefix, name in _PLATFORM_PREFIXES:
        if sys.platform.startswith(prefix):
            return name
    return sys.platform


@dataclass
class Requirements:
    """What a backend needs to run, structured for an agent to act on."""

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
    credentials: List[str] = field(default_factory=list)  # "export VAR  (get a key)"
    notes: List[str] = field(default_factory=list)
    verify_command: Optional[str] = None  # one shell line that checks the result
    alternative_label: str = "Lighter alternative"

    def instructions(self) -> str:
        """An agent- and human-readable, copy-pasteable install plan."""
        if self.available:
            return f"'{self.backend_id}' is already installed and usable. ✓"
        lines = [f"To use the '{self.backend_id}' backend:"]
        n = 1
        if self.system:
            lines.append(f"  {n}. System dependency:")
            lines.extend(f"       {cmd}" for cmd in self.system)
            if self.system_note:
                lines.append(f"     ({self.system_note})")
            n += 1
        lines.append(f"  {n}. {self.pip_command}")
        if self.gpu:
            lines.append(f"       GPU: {self.gpu}")
        n += 1
        if self.credentials:
            lines.append(f"  {n}. Set credential(s):")
            lines.extend(f"       {c}" for c in self.credentials)
            n += 1
        if self.weights:
            lines.append(f"  • {self.weights}")
        if self.heavy:
            lines.append(
                "  • Note: large download (deep-learning framework + weights)."
            )
        if self.alternative:
            lines.append(f"  • {self.alternative_label}: {self.alternative}.")
        lines.extend(f"  • {note}" for note in self.notes)
        if self.verify_command:
            lines.append(f"Verify:   {self.verify_command}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.instructions()


def build_requirements(
    backend_id: str,
    *,
    package: str,
    implemented: bool,
    available: bool,
    recipe: Optional[Mapping] = None,
    is_local: bool = False,
    is_remote: bool = False,
    ledger_pip: str = "",
    credentials: Iterable[str] = (),
    platform: Optional[str] = None,
    verify_command: Optional[str] = None,
    unimplemented_note: Optional[str] = None,
    alternative_label: str = "Lighter alternative",
) -> Requirements:
    """Build :class:`Requirements` for ``backend_id`` from its recipe and known facts.

    Args:
        backend_id: The backend's id.
        package: The distribution whose extra installs it (``pip install "pkg[x]"``).
        implemented: Whether the package ships a facade for it.
        available: Whether it is usable right now (the package's own probe).
        recipe: Its row of the package's recipes table (see the module docstring).
        is_local / is_remote: From the backend's config or ledger record.
        ledger_pip: The ledger's install line, used for a backend not implemented.
        credentials: ``export`` lines (see :func:`~ocracy.kit.credentials.credential_lines`).
        platform: Override :func:`current_platform` (for tests and docs).
        verify_command: The shell line shown as ``Verify:``.
        unimplemented_note: Appended to ``notes`` when not implemented.
        alternative_label: The wording before ``alt`` in the instructions.
    """
    recipe = dict(recipe or {})
    extra = recipe.get("extra") or (backend_id if implemented else None)
    if implemented and extra:
        pip_command = f'pip install "{package}[{extra}]"'
    else:
        pip_command = (
            ledger_pip or ""
        ).strip() or f'pip install "{package}[{backend_id}]"'
    notes = list(recipe.get("notes", []))
    if not implemented and unimplemented_note:
        notes.append(unimplemented_note)
    return Requirements(
        backend_id=backend_id,
        implemented=implemented,
        available=available,
        is_local=is_local,
        is_remote=is_remote,
        pip_command=pip_command,
        extra=extra,
        system=list(recipe.get("system", {}).get(platform or current_platform(), [])),
        system_note=recipe.get("system_note"),
        gpu=recipe.get("gpu"),
        weights=recipe.get("weights"),
        heavy=bool(recipe.get("heavy")),
        alternative=recipe.get("alt"),
        credentials=list(credentials),
        notes=notes,
        verify_command=verify_command,
        alternative_label=alternative_label,
    )


def run_install(
    req: Requirements,
    *,
    package: str,
    yes: bool = False,
    verify_code: Optional[str] = None,
    upgrade: bool = False,
) -> dict:
    """Plan (default) or run (``yes=True``) the pip install that ``req`` describes.

    Args:
        req: The plan, from :func:`build_requirements`.
        package: The distribution whose extra to install.
        yes: Actually run pip; otherwise a dry run that changes nothing.
        verify_code: Python source run in a fresh interpreter after a successful
            install; ``available_after`` is whether it printed ``True``.
        upgrade: Pass ``--upgrade`` to pip.

    Returns:
        ``{backend, requirements, ran, available_before, message?, pip_argv?,
        returncode?, stdout_tail?, stderr_tail?, available_after?, system_todo?}``.
    """
    result = {
        "backend": req.backend_id,
        "requirements": req,
        "ran": False,
        "available_before": req.available,
    }
    if req.available:
        result["message"] = f"'{req.backend_id}' is already available — nothing to do."
        return result
    if not req.implemented:
        result["message"] = req.instructions()
        return result
    if not yes:
        result["message"] = (
            "Dry run — pass yes=True to run the pip install.\n" + req.instructions()
        )
        return result

    import subprocess  # only an actual install pays for it

    python = sys.executable  # the running interpreter, read at call time
    target = f"{package}[{req.extra}]" if req.extra else req.backend_id
    cmd = [python, "-m", "pip", "install", *(["--upgrade"] if upgrade else []), target]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result.update(
        ran=True,
        pip_argv=cmd,
        returncode=proc.returncode,
        stdout_tail=proc.stdout[-OUTPUT_TAIL_CHARS:],
        stderr_tail=proc.stderr[-OUTPUT_TAIL_CHARS:],
    )
    if verify_code and proc.returncode == 0:
        # Importability is cached per process; probe in a fresh interpreter.
        probe = subprocess.run(
            [python, "-c", verify_code], capture_output=True, text=True
        )
        result["available_after"] = probe.stdout.strip() == "True"
    if req.system:
        result["system_todo"] = req.system
    return result
