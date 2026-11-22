"""Coverage-pass tests for the CLI tool functions that wrap ``ocracy.ocr`` and the installer."""

import json

import pytest

import ocracy
from ocracy import tools
from ocracy.base import BBox, OcrResult, TextBlock


@pytest.fixture
def fake_ocr(monkeypatch):
    seen = {}
    result = OcrResult(
        text="hello",
        blocks=[
            TextBlock("hello", bbox=BBox(0, 1, 2, 3), confidence=0.9, level="word")
        ],
        backend="fake",
    )

    def ocr(image, *, backend=None, **kwargs):
        seen.update(image=image, backend=backend, kwargs=kwargs)
        return result

    monkeypatch.setattr(ocracy, "ocr", ocr)
    return seen, result


def test_read_text_is_the_default_output(fake_ocr):
    seen, _ = fake_ocr
    assert tools.read("a.png", backend="fake", languages="en, fr,") == "hello"
    assert seen["kwargs"] == {"languages": ["en", "fr"]}


def test_read_json_carries_backend_text_and_blocks(fake_ocr):
    out = json.loads(tools.read("a.png", output="json"))
    assert out["backend"] == "fake" and out["text"] == "hello"
    assert out["blocks"] == [
        {"text": "hello", "level": "word", "confidence": 0.9, "bbox": [0, 1, 2, 3]}
    ]


def test_read_json_block_without_a_bbox_is_null(fake_ocr, monkeypatch):
    seen, result = fake_ocr
    result.blocks[0].bbox = None
    assert json.loads(tools.read("a.png", output="json"))["blocks"][0]["bbox"] is None


def test_read_markdown_falls_back_to_text(fake_ocr):
    assert tools.read("a.png", output="markdown") == "hello"


def test_split_csv_handles_empty_and_blank_items():
    assert tools._split_csv(None) is None and tools._split_csv("") is None
    assert tools._split_csv(" a , ,b") == ["a", "b"]


class _Req:
    def instructions(self):
        return "REQS"


def test_install_reports_success_failure_and_plan(monkeypatch):
    def fake(result):
        monkeypatch.setattr(ocracy, "install", lambda *a, **k: result)

    fake({"ran": True, "available_after": True})
    assert "ready" in tools.install("x", yes=True)
    fake(
        {"ran": True, "available_after": False, "returncode": 2, "requirements": _Req()}
    )
    out = tools.install("x", yes=True)
    assert "pip exit 2" in out and out.endswith("REQS")
    fake({"message": "plan only", "requirements": _Req()})
    assert tools.install("x") == "plan only"
    fake({"requirements": _Req()})
    assert tools.install("x") == "REQS"


def test_doctor_lists_available_and_missing(monkeypatch):
    monkeypatch.setattr(
        ocracy,
        "doctor",
        lambda: {"available": ["a"], "missing": {"b": "pip install b"}},
    )
    out = tools.doctor()
    assert "✓ a" in out and "✗ b" in out and "pip install b" in out
    monkeypatch.setattr(ocracy, "doctor", lambda: {"available": [], "missing": {}})
    assert "(none)" in tools.doctor()


def test_requirements_prints_the_instructions(monkeypatch):
    monkeypatch.setattr(ocracy, "requirements", lambda bid, gpu=False: _Req())
    assert tools.requirements("x") == "REQS"


def test_status_levels_and_names():
    assert tools.status(level="implemented")
    out = tools.status(names=True)
    assert "implemented (" in out and "tested (" in out


def test_main_dispatches_through_cw_or_exits(monkeypatch):
    pytest.importorskip("cw")
    from ocracy import __main__ as entry

    monkeypatch.setattr("sys.argv", ["ocracy", "backends"])
    with pytest.raises(SystemExit) as exc:
        entry.main()
    assert exc.value.code in (0, None)
