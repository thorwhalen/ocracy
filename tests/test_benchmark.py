"""The benchmark verb: corpus loading, scoring seams, failure isolation, the CLI tool."""

import json
from types import SimpleNamespace

import pytest

import ocracy
from ocracy import tools
from ocracy.benchmark import cer, edit_distance, load_corpus, summary, wer


def fake_read(texts):
    """A reader returning ``texts[backend]`` (an Exception instance is raised)."""

    def read(image, *, backend, **kw):
        out = texts[backend]
        if isinstance(out, Exception):
            raise out
        return SimpleNamespace(text=out)

    return read


def test_metrics():
    assert edit_distance("kitten", "sitting") == 3
    assert cer("hello", "hallo") == pytest.approx(0.2)
    assert cer("", "") == 0.0 and cer("", "x") == 1.0
    assert wer("the cat sat", "the cat") == pytest.approx(1 / 3)


def test_rows_per_backend_and_image_with_failures_isolated():
    corpus = {"a.png": "hello world", "b.png": "foo"}
    read = fake_read({"good": "hello world", "bad": RuntimeError("boom")})
    rows = ocracy.benchmark(corpus, ["good", "bad"], read=read)
    assert [(r["backend"], r["image"]) for r in rows] == [
        ("good", "a.png"), ("good", "b.png"), ("bad", "a.png"), ("bad", "b.png"),
    ]
    good_a, good_b, bad_a, _ = rows
    assert good_a["cer"] == 0.0 and good_a["error"] is None and good_a["seconds"] >= 0
    assert good_b["cer"] > 0 and good_b["hypothesis"] == "hello world"
    assert bad_a["cer"] is None and bad_a["hypothesis"] is None
    assert bad_a["error"] == "RuntimeError: boom"


def test_whitespace_is_normalized_and_normalize_is_a_seam():
    corpus = {"a.png": "hello\nworld"}
    read = fake_read({"x": "hello   world"})
    assert ocracy.benchmark(corpus, "x", read=read)[0]["cer"] == 0.0
    strict = ocracy.benchmark(corpus, "x", read=read, normalize=lambda s: s)
    assert strict[0]["cer"] > 0


def test_metric_seam_callable_and_mapping():
    corpus = {"a.png": "abc"}
    read = fake_read({"x": "abd"})
    (row,) = ocracy.benchmark(corpus, "x", read=read, metric=lambda r, h: 42.0)
    assert row["score"] == 42.0 and "cer" not in row
    (row,) = ocracy.benchmark(corpus, "x", read=read, metric={"len": lambda r, h: len(h)})
    assert row["len"] == 3


def test_read_kwargs_reach_the_reader():
    seen = {}

    def read(image, *, backend, **kw):
        seen.update(kw)
        return SimpleNamespace(text="a")

    ocracy.benchmark({"a.png": "a"}, "x", read=read, languages=["fr"])
    assert seen == {"languages": ["fr"]}


def test_corpus_from_folder_and_json_file(tmp_path):
    (tmp_path / "truth.json").write_text(json.dumps({"a.png": "hi"}))
    expected = {str(tmp_path / "a.png"): "hi"}
    assert load_corpus(tmp_path) == expected
    assert load_corpus(tmp_path / "truth.json") == expected
    with pytest.raises(FileNotFoundError):
        load_corpus(tmp_path / "nope")


def test_default_backends_are_the_installed_ones(monkeypatch):
    import sys

    monkeypatch.setattr(sys.modules["ocracy.install"], "available_backends", lambda: ["only"])
    rows = ocracy.benchmark({"a.png": "a"}, read=fake_read({"only": "a"}))
    assert {r["backend"] for r in rows} == {"only"}


def test_summary_table():
    rows = ocracy.benchmark(
        {"a.png": "abc"}, ["good", "bad"],
        read=fake_read({"good": "abc", "bad": RuntimeError("x")}),
    )
    lines = summary(rows).splitlines()
    assert lines[0].split()[:3] == ["backend", "cer", "wer"]
    assert lines[1].split()[0] == "good" and lines[1].split()[-1] == "1/0"
    assert lines[2].split()[-1] == "0/1"


def test_tool_verb_runs_on_the_registered_reader(tmp_path, monkeypatch):
    (tmp_path / "truth.json").write_text(json.dumps({"a.png": "hi"}))
    monkeypatch.setattr(ocracy, "ocr", lambda image, *, backend=None, **kw: SimpleNamespace(text="hi"))
    # benchmark() looks ``ocr`` up on the package at call time
    rows = json.loads(tools.benchmark(str(tmp_path), backends="t", output="json"))
    assert rows[0]["backend"] == "t" and rows[0]["cer"] == 0.0
    assert "t" in tools.benchmark(str(tmp_path), backends="t")
    assert tools.benchmark in tools._dispatch_funcs
