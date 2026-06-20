"""Tests for the facade-building abstraction tools."""

import importlib.util

import pytest

from ocracy.base import BBox
from ocracy.make_backend import (
    as_bbox,
    make_block,
    normalize_confidence,
    scaffold_backend,
)

HAS_PIL = importlib.util.find_spec("PIL") is not None


def test_normalize_confidence_scales_and_clips():
    assert normalize_confidence(None) is None
    assert normalize_confidence(95, scale=100) == 0.95
    assert normalize_confidence(150, scale=100) == 1.0  # clipped
    assert normalize_confidence(-5, scale=100) == 0.0  # clipped


def test_as_bbox_accepts_shapes():
    assert as_bbox(None) is None
    b = as_bbox((1, 2, 3, 4))
    assert isinstance(b, BBox) and b.as_tuple == (1, 2, 3, 4)
    poly = as_bbox([(0, 0), (2, 0), (2, 2), (0, 2)])
    assert poly.as_tuple == (0, 0, 2, 2)
    assert as_bbox(b) is b  # pass-through


def test_make_block_normalizes():
    blk = make_block("hi", bbox=(0, 0, 10, 10), confidence=88, conf_scale=100, line=3)
    assert blk.text == "hi"
    assert blk.confidence == 0.88
    assert blk.level == "word"
    assert blk.bbox.as_tuple == (0, 0, 10, 10)
    assert blk.meta["line"] == 3


def test_scaffold_backend_from_ledger(tmp_path):
    dest = scaffold_backend("google-vision", dest=tmp_path / "google_vision")
    config_text = (dest / "config.py").read_text()
    # id/name rewritten from the template; ledger values pulled in.
    assert '"id": "google-vision"' in config_text
    assert '"is_remote": True' in config_text
    assert '"is_local": False' in config_text
    assert "__template__" not in config_text
    # import_name / pip_install are rewritten even though their TEMPLATE lines
    # carry a trailing usage hint (regression guard for the regex fix).
    assert '"PACKAGE"' not in config_text
    assert '"import_name": "google_vision"' in config_text
    # adapter + __init__ created
    assert (dest / "adapter.py").exists()
    assert (dest / "__init__.py").exists()


def test_scaffold_refuses_overwrite(tmp_path):
    d = tmp_path / "x"
    scaffold_backend("tesseract", dest=d)
    with pytest.raises(FileExistsError):
        scaffold_backend("tesseract", dest=d)


@pytest.mark.skipif(not HAS_PIL, reason="Pillow not installed")
def test_make_test_image_and_validate_reports_unavailable_gracefully():
    from ocracy.make_backend import validate_adapter

    # Even if the tesseract binary is missing, validate_adapter must not raise;
    # it returns a report dict describing what happened.
    report = validate_adapter("tesseract")
    assert report["backend"] == "tesseract"
    assert "available" in report and "ok" in report
