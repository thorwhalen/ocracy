"""Tests for the install/requirements helpers (no engines or network needed).

These exercise the *guidance* layer, not real installs. We assert against
backends that are not installed in CI (e.g. paddleocr, google-vision) for the
"not available" content, and structural facts for the rest.
"""

import ocracy
from ocracy.install import Requirements


def test_requirements_structure_for_tesseract():
    req = ocracy.requirements("tesseract")
    assert isinstance(req, Requirements)
    assert req.implemented is True
    assert req.is_local is True
    assert 'ocracy[tesseract]' in req.pip_command
    # Tesseract needs a system binary on every OS.
    assert req.system, "expected a system-dependency command for tesseract"
    assert isinstance(req.instructions(), str) and req.instructions()


def test_requirements_paddleocr_flags_heavy_and_alternative():
    # paddleocr is not installed in dev/CI, so we get the full plan.
    req = ocracy.requirements("paddleocr")
    assert req.heavy is True
    assert req.alternative and "rapidocr" in req.alternative
    text = req.instructions()
    assert 'ocracy[paddleocr]' in text
    assert "rapidocr" in text  # the lighter alternative is surfaced


def test_requirements_gpu_note():
    req = ocracy.requirements("paddleocr", gpu=True)
    assert req.gpu and "paddlepaddle-gpu" in req.gpu


def test_requirements_remote_surfaces_credentials_with_link():
    req = ocracy.requirements("google-vision")
    assert req.is_remote is True
    assert req.credentials, "remote backend should surface credential env vars"
    joined = " ".join(req.credentials)
    assert "GOOGLE_APPLICATION_CREDENTIALS" in joined
    assert "http" in joined  # the 'get a key' link


def test_requirements_listed_only_backend():
    # surya is in the ledger but ocracy ships no facade for it.
    req = ocracy.requirements("surya")
    assert req.implemented is False
    assert req.pip_command  # from the ledger's python_install
    assert any("ocracy-add-backend" in n for n in req.notes)


def test_check_returns_bool():
    assert isinstance(ocracy.check("tesseract"), bool)


def test_doctor_partitions_all_implemented_backends():
    rep = ocracy.doctor()
    assert set(rep) == {"available", "missing"}
    covered = set(rep["available"]) | set(rep["missing"])
    assert covered == set(ocracy.list_backends())


def test_install_dry_run_changes_nothing():
    res = ocracy.install("paddleocr", yes=False)  # dry run
    assert res["ran"] is False
    assert isinstance(res["requirements"], Requirements)
    assert "yes=True" in res["message"] or not res["available_before"]
