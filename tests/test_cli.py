"""Tests for the CLI tools (invoked as functions; no ``cw`` needed for these)."""

import importlib.util
import json
import os

import pytest

from ocracy import tools

HAS_CW = importlib.util.find_spec("cw") is not None


def test_backends_lists_implemented():
    out = tools.backends()
    assert "tesseract" in out
    # capability filter narrows the list
    math_out = tools.backends(capability="math")
    assert "mathpix" in math_out
    assert "tesseract" not in math_out


def test_find_composes_flags():
    out = tools.find(local=True, free=True)
    assert "tesseract" in out
    assert "google-vision" not in out  # remote, filtered out
    # the implemented marker shows for built backends
    assert "[✓]" in out


def test_info_returns_json_record():
    rec = json.loads(tools.info("google-vision"))
    assert rec["id"] == "google-vision"
    assert rec["is_remote"] is True


def test_scaffold_via_cli(tmp_path):
    msg = tools.scaffold("surya", dest=str(tmp_path / "surya"))
    assert "Scaffolded" in msg
    assert (tmp_path / "surya" / "config.py").exists()


def test_validate_returns_json_report():
    rep = json.loads(tools.validate("tesseract"))
    assert rep["backend"] == "tesseract"
    assert "ok" in rep


def test_dispatch_funcs_is_sound():
    # The SSOT list the CLI dispatches must be all callables with docstrings.
    assert tools._dispatch_funcs
    for f in tools._dispatch_funcs:
        assert callable(f) and (f.__doc__ or "").strip(), f.__name__


@pytest.mark.skipif(not HAS_CW, reason="cw (cli extra) not installed")
def test_python_m_ocracy_runs():
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-m", "ocracy", "backends"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert "tesseract" in out.stdout


@pytest.mark.skipif(not HAS_CW, reason="cw (cli extra) not installed")
@pytest.mark.parametrize("command", [f.__name__ for f in tools._dispatch_funcs])
def test_every_subcommand_has_help(command):
    """``ocracy <command> --help`` must build and render for every dispatched tool."""
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "-m", "ocracy", command, "--help"],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert f"{command} [-h]" in out.stdout


def test_friendly_error_when_cli_extra_missing(tmp_path):
    """Without the ``[cli]`` extra the CLI must explain itself, not traceback.

    ``import ocracy`` is dependency-free by design, so the entry point has to survive
    the CLI dependency being absent. Masking it with a module that raises ImportError
    is the portable way to exercise that branch without uninstalling anything.
    """
    import subprocess
    import sys

    (tmp_path / "cw.py").write_text("raise ImportError('masked for test')\n")
    env = dict(os.environ, PYTHONPATH=str(tmp_path))
    out = subprocess.run(
        [sys.executable, "-m", "ocracy", "backends"],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert out.returncode == 1
    assert "The ocracy CLI requires 'cw'" in out.stderr
    assert "pip install 'ocracy[cli]'" in out.stderr
    assert "Traceback" not in out.stderr
