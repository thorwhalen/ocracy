"""PaddleOCR adapters without PaddleOCR: the 3.x/2.x shapes and PP-StructureV3.

A fake ``paddleocr`` module stands in for the engine, so these run in CI where
PaddlePaddle is not installed. The measurements behind the two backends are on
https://github.com/thorwhalen/ocracy/issues/1.
"""

import sys
import types

import pytest

from ocracy.backends.paddleocr import adapter as paddle_adapter
from ocracy.backends.paddleocr.adapter import blocks_from_v2, blocks_from_v3
from ocracy.backends.paddleocr.config import BACKEND_CONFIG as PADDLE_CFG
from ocracy.backends.paddleocr_ppstructure import adapter as structure_adapter
from ocracy.backends.paddleocr_ppstructure.config import BACKEND_CONFIG as STRUCT_CFG

POLY = [[0, 0], [10, 0], [10, 5], [0, 5]]
V3_PAGE = {
    "rec_texts": ["Item", "Qty"],
    "rec_scores": [0.9, 0.8],
    "rec_polys": [POLY, POLY],
}


class _Result(dict):
    """Like PaddleOCR's result objects: dict access plus a ``markdown`` attribute."""

    markdown = {"markdown_texts": "\n<table><tr><td>Item</td></tr></table>\n"}


@pytest.fixture
def fake_paddle(monkeypatch):
    """Install a fake ``paddleocr`` 3.x module; ``calls`` records what was built."""
    calls = []

    class PaddleOCR:
        def __init__(self, **kw):
            if "show_log" in kw:  # what 3.x does with a 2.x keyword
                raise ValueError("Unknown argument: show_log")
            calls.append(("PaddleOCR", kw))

        def predict(self, arr, **kw):
            return [_Result(V3_PAGE)]

    class PPStructureV3:
        def __init__(self, **kw):
            calls.append(("PPStructureV3", kw))

        def predict(self, arr, **kw):
            return [_Result(overall_ocr_res=V3_PAGE, parsing_res_list=["table"])]

    module = types.SimpleNamespace(PaddleOCR=PaddleOCR, PPStructureV3=PPStructureV3)
    monkeypatch.setitem(sys.modules, "paddleocr", module)
    monkeypatch.setattr("ocracy.util.to_numpy", lambda image: image)
    return calls


def test_v3_and_v2_result_shapes_become_line_blocks():
    v3 = blocks_from_v3(V3_PAGE)
    assert [b.text for b in v3] == ["Item", "Qty"] and v3[0].level == "line"
    assert v3[0].confidence == pytest.approx(0.9) and v3[0].bbox.x1 == 10
    v2 = blocks_from_v2([[POLY, ("Item", 0.9)], "junk", [POLY, ("Qty", 0.8)]])
    assert [b.text for b in v2] == ["Item", "Qty"]
    assert blocks_from_v3({}) == [] and blocks_from_v2(None) == []


def test_paddleocr_uses_the_3x_api_with_preprocessors_off(fake_paddle):
    r = paddle_adapter.Adapter(PADDLE_CFG).read("img", languages=["fr"])
    assert [b.text for b in r.lines] == ["Item", "Qty"] and r.words == []
    ((name, kw),) = fake_paddle
    assert name == "PaddleOCR" and kw["lang"] == "fr"  # 3.x takes ISO codes
    assert kw["use_doc_unwarping"] is False and "show_log" not in kw


def test_paddleocr_uses_the_2x_api_when_there_is_no_predict(monkeypatch):
    built = []

    class PaddleOCR:  # 2.x: accepts any keyword, has ocr() but no predict()
        def __init__(self, **kwargs):
            built.append(kwargs)

        def ocr(self, arr, cls=True):
            return [[[POLY, ("Old", 0.7)]]]

    monkeypatch.setitem(
        sys.modules, "paddleocr", types.SimpleNamespace(PaddleOCR=PaddleOCR)
    )
    monkeypatch.setattr("ocracy.util.to_numpy", lambda image: image)
    r = paddle_adapter.Adapter(PADDLE_CFG).read("img", languages=["ru"])
    assert [b.text for b in r.lines] == ["Old"]
    assert built == [{"use_angle_cls": True, "lang": "cyrillic", "show_log": False}]


def test_language_codes_per_version():
    from ocracy.backends.paddleocr.config import V2_LANG, V3_LANG, first_language

    assert first_language(None) == "en" and first_language(["ZH-TW", "en"]) == "zh-tw"
    assert V3_LANG.get("zh-tw") == "chinese_cht" and "ru" not in V3_LANG  # 3.x: ISO
    assert V2_LANG["ru"] == "cyrillic" and V2_LANG["fr"] == "french"


def test_ppstructure_returns_markdown_and_lines(fake_paddle):
    r = structure_adapter.Adapter(STRUCT_CFG).read("img")
    assert r.markdown == "<table><tr><td>Item</td></tr></table>"
    assert [b.text for b in r.lines] == ["Item", "Qty"] and r.text == "Item\nQty"
    assert set(STRUCT_CFG["capabilities"]) >= {"tables", "layout"}


def test_ppstructure_missing_doc_parser_names_the_install(monkeypatch, fake_paddle):
    def broken(**kw):
        raise RuntimeError("A dependency error occurred during pipeline creation.")

    monkeypatch.setattr(sys.modules["paddleocr"], "PPStructureV3", broken)
    with pytest.raises(ImportError, match=r"ocracy\[paddleocr-ppstructure\]"):
        structure_adapter.Adapter(STRUCT_CFG).read("img")


def test_ppstructure_is_implemented_and_rapidocr_lacks_its_capabilities():
    import ocracy

    assert ocracy.catalog["paddleocr-ppstructure"].implemented
    assert "paddleocr-ppstructure" in ocracy.list_backends()
    rapid = ocracy.registry.get_config("rapidocr")["capabilities"]
    assert not set(STRUCT_CFG["capabilities"]) & set(rapid)
