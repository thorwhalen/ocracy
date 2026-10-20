"""The rapidocr adapter on 3.x and on the legacy package, with fake modules.

Fakes stand in for the engines so these run where neither is installed. The
measurements behind the 3.x move are on https://github.com/thorwhalen/ocracy/issues/22.
"""

import sys
import types

import pytest

import ocracy
from ocracy.backends.rapidocr import adapter as rapid_adapter
from ocracy.backends.rapidocr.adapter import Adapter, blocks_from_legacy, blocks_from_v3
from ocracy.backends.rapidocr.config import BACKEND_CONFIG, MODEL_SIZES

BOX = [[0, 0], [10, 0], [10, 5], [0, 5]]


class _Result:
    def __init__(self, boxes=None, txts=None, scores=None):
        self.boxes, self.txts, self.scores = boxes, txts, scores


@pytest.fixture
def fake_v3(monkeypatch):
    """A fake ``rapidocr`` 3.x module; ``built`` records each ``params`` it was built with."""
    built = []

    class RapidOCR:
        def __init__(self, params=None):
            built.append(params)

        def __call__(self, arr, **extra):
            return _Result([BOX, BOX], ["Invoice 2024", "issued on 14 March"], [0.99, 0.95])

    mod = types.ModuleType("rapidocr")
    mod.RapidOCR = RapidOCR
    mod.OCRVersion = lambda v: ("version", v)
    mod.ModelType = lambda v: ("size", v)
    monkeypatch.setitem(sys.modules, "rapidocr", mod)
    monkeypatch.delitem(sys.modules, "rapidocr_onnxruntime", raising=False)
    return built


@pytest.fixture
def fake_legacy(monkeypatch):
    class RapidOCR:
        def __call__(self, arr, **extra):
            return [[BOX, "old text", 0.9]], 0.1

    mod = types.ModuleType("rapidocr_onnxruntime")
    mod.RapidOCR = RapidOCR
    monkeypatch.setitem(sys.modules, "rapidocr_onnxruntime", mod)
    monkeypatch.setitem(sys.modules, "rapidocr", None)  # import raises ImportError


def _image():
    pytest.importorskip("numpy")
    import numpy as np

    return np.full((20, 40, 3), 255, np.uint8)


def test_v3_blocks_are_lines_with_boxes_and_confidence():
    blocks = blocks_from_v3(_Result([BOX], ["hello"], [0.5]))
    assert [(b.text, b.level, b.confidence) for b in blocks] == [("hello", "line", 0.5)]
    assert blocks_from_v3(_Result()) == []  # 3.x gives None everywhere for an empty page
    assert blocks_from_v3(None) == []


def test_legacy_blocks_and_empty():
    assert [b.text for b in blocks_from_legacy([[BOX, "x", 0.8]])] == ["x"]
    assert blocks_from_legacy(None) == []


def test_default_builds_ppocrv6_medium_in_english(fake_v3):
    result = Adapter(BACKEND_CONFIG)._read(_image())
    assert [b.text for b in result.blocks] == ["Invoice 2024", "issued on 14 March"]
    (params,) = fake_v3
    assert params["Rec.lang_type"] == "en"
    assert params["Det.model_type"] == params["Rec.model_type"] == ("size", "medium")
    assert params["Rec.ocr_version"] == ("version", "PP-OCRv6")


def test_languages_and_model_size_reach_the_engine_through_ocr(fake_v3):
    ocracy.ocr(_image(), backend="rapidocr", languages=["fr", "en"], model_size="small")
    assert fake_v3[-1]["Rec.lang_type"] == "fr"
    assert fake_v3[-1]["Rec.model_type"] == ("size", "small")


def test_one_engine_is_cached_per_language_and_size(fake_v3):
    a = Adapter(BACKEND_CONFIG)
    for lang, size in [("en", "medium"), ("en", "medium"), ("fr", "medium"), ("en", "tiny")]:
        a._read(_image(), lang=lang, model_size=size)
    assert len(fake_v3) == 3


def test_an_unknown_model_size_is_refused_with_the_choices(fake_v3):
    with pytest.raises(Exception, match="tiny"):
        ocracy.ocr(_image(), backend="rapidocr", model_size="huge")


def test_a_legacy_only_install_still_reads(fake_legacy):
    result = Adapter(BACKEND_CONFIG)._read(_image(), lang="fr", model_size="tiny")
    assert [b.text for b in result.blocks] == ["old text"]


def test_a_legacy_only_install_counts_as_available(fake_legacy):
    assert ocracy.registry._is_available("rapidocr")


def test_the_config_declares_the_new_package_and_the_legacy_alternative():
    assert BACKEND_CONFIG["import_name"] == "rapidocr"
    assert BACKEND_CONFIG["import_alternatives"] == ["rapidocr_onnxruntime"]
    assert MODEL_SIZES == ("tiny", "small", "medium")


def test_real_engine_reads_clean_print_with_word_spaces():
    pytest.importorskip("rapidocr")
    PIL = pytest.importorskip("PIL.Image")
    from PIL import ImageDraw, ImageFont

    im = PIL.new("RGB", (700, 100), "white")
    font = None
    try:
        font = ImageFont.load_default(size=36)
    except TypeError:
        pass
    ImageDraw.Draw(im).text((20, 25), "Invoice issued on 14 March", fill="black", font=font)
    text = ocracy.read_text(im, backend="rapidocr", model_size="small")
    assert "14" in text and "March" in text


def test_an_empty_language_list_means_english():
    from ocracy.backends.paddleocr.config import first_language

    assert first_language([]) == "en"


def test_a_rapidocr_without_3x_model_selection_is_not_taken_for_3x(monkeypatch):
    old = types.ModuleType("rapidocr")  # no OCRVersion
    monkeypatch.setitem(sys.modules, "rapidocr", old)
    assert not rapid_adapter.is_v3_package()
