"""Tests for the normalized result types (no engine/Pillow needed)."""

from ocracy.base import BBox, OcrResult, TextBlock


def test_bbox_geometry_and_constructors():
    b = BBox(10, 20, 40, 60)
    assert b.width == 30 and b.height == 40
    assert b.area == 1200
    assert b.xywh == (10, 20, 30, 40)
    assert b.as_tuple == (10, 20, 40, 60)

    assert BBox.from_xywh(10, 20, 30, 40) == b

    poly = BBox.from_polygon([(0, 0), (10, 0), (10, 5), (0, 5)])
    assert poly.as_tuple == (0, 0, 10, 5)
    assert poly.polygon == ((0, 0), (10, 0), (10, 5), (0, 5))


def test_ocrresult_from_blocks_assembles_text_and_views():
    blocks = [
        TextBlock("Hello", confidence=0.9, level="word"),
        TextBlock("world", confidence=0.5, level="word"),
        TextBlock("Hello world", confidence=0.7, level="line"),
    ]
    res = OcrResult.from_blocks(blocks, backend="x", text="Hello world")
    assert str(res) == "Hello world"
    assert res.text == "Hello world"
    assert len(res.words) == 2
    assert len(res.lines) == 1
    assert list(res) == blocks  # iteration yields blocks
    assert abs(res.mean_confidence - (0.9 + 0.5 + 0.7) / 3) < 1e-9
    assert bool(res) is True


def test_from_text_minimal():
    res = OcrResult.from_text("just text", backend="x", pages=1)
    assert res.text == "just text"
    assert res.blocks == []
    assert res.meta["pages"] == 1
    assert res.mean_confidence is None


def test_filter_confidence_rebuilds():
    blocks = [
        TextBlock("keep", confidence=0.9, level="word"),
        TextBlock("drop", confidence=0.2, level="word"),
        TextBlock("noconf", confidence=None, level="word"),
    ]
    res = OcrResult.from_blocks(blocks, backend="x")
    filtered = res.filter_confidence(0.5)
    assert [b.text for b in filtered.blocks] == ["keep"]
    assert filtered.text == "keep"
