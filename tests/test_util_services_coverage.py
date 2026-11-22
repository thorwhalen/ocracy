"""Coverage-pass tests: image-input helpers, service handles, and a REST adapter with a fake ``requests``."""

import os
import sys
import types

import pytest

import ocracy
from ocracy import util
from ocracy.services import ServiceCollection, services

PIL = pytest.importorskip("PIL.Image")
np = pytest.importorskip("numpy")


def _png_bytes():
    import io

    buf = io.BytesIO()
    PIL.new("RGB", (2, 3), "white").save(buf, format="PNG")
    return buf.getvalue()


# --- util ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, kind",
    [
        (b"x", "bytes"),
        (bytearray(b"x"), "bytes"),
        ("http://a/b.png", "url"),
        ("HTTPS://a/b.png", "url"),
        ("a/b.png", "path"),
    ],
)
def test_classify_input_structural_kinds(value, kind):
    assert util.classify_input(value) == kind


def test_classify_input_pil_numpy_and_unsupported():
    assert util.classify_input(PIL.new("RGB", (1, 1))) == "pil"
    assert util.classify_input(np.zeros((1, 1))) == "numpy"
    with pytest.raises(TypeError, match="Unsupported image input"):
        util.classify_input(object())


def test_is_url_is_false_for_non_strings():
    assert util.is_url(b"http://x") is False and util.is_url(None) is False


def test_to_pil_from_every_kind(tmp_path, monkeypatch):
    data = _png_bytes()
    p = tmp_path / "i.png"
    p.write_bytes(data)
    pil = PIL.new("RGB", (2, 3))
    assert util.to_pil(pil) is pil
    assert util.to_pil(data).size == (2, 3)
    assert util.to_pil(p).size == (2, 3)
    assert util.to_pil(np.zeros((3, 2, 3), dtype="uint8")).size == (2, 3)
    monkeypatch.setattr(util, "_fetch_url", lambda url, **kw: data)
    assert util.to_pil("http://x/i.png").size == (2, 3)


def test_to_numpy_passes_arrays_through_and_converts_others():
    arr = np.zeros((3, 2), dtype="uint8")
    assert util.to_numpy(arr) is arr
    assert util.to_numpy(_png_bytes()).shape[:2] == (3, 2)


def test_load_image_bytes_for_each_kind(tmp_path, monkeypatch):
    data = _png_bytes()
    p = tmp_path / "i.png"
    p.write_bytes(data)
    assert util.load_image_bytes(data) == data
    assert util.load_image_bytes(p) == data
    monkeypatch.setattr(util, "_fetch_url", lambda url, **kw: data)
    assert util.load_image_bytes("http://x/i.png") == data
    encoded = util.load_image_bytes(PIL.new("RGB", (2, 3)))
    assert PIL.open(__import__("io").BytesIO(encoded)).size == (2, 3)


def test_image_path_keeps_real_paths_and_cleans_temp_files(tmp_path):
    p = tmp_path / "i.png"
    p.write_bytes(_png_bytes())
    with util.image_path(str(p)) as same:
        assert same == str(p)
    assert p.exists()
    with util.image_path(_png_bytes(), suffix=".jpg") as temp:
        assert temp.endswith(".jpg") and os.path.exists(temp)
    assert not os.path.exists(temp)


def test_cleanup_temp_ignores_missing_files_and_non_temp(tmp_path):
    util.cleanup_temp(str(tmp_path / "gone"), True)  # no error
    keep = tmp_path / "keep"
    keep.write_text("x")
    util.cleanup_temp(str(keep), False)
    assert keep.exists()


def test_fetch_url_reads_the_response(monkeypatch):
    import urllib.request

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return b"payload"

    monkeypatch.setattr(urllib.request, "urlopen", lambda url, timeout: Resp())
    assert util._fetch_url("http://x") == b"payload"


# --- services --------------------------------------------------------------------------


def test_service_collection_is_a_lazy_mapping():
    assert "tesseract" in services and "nope" not in services
    assert len(services) == len(list(services)) > 0
    assert list(services) == sorted(services)
    handle = services["tesseract"]
    assert services["tesseract"] is handle  # cached
    assert repr(handle).startswith("<ServiceHandle 'tesseract'")
    assert "tesseract" in repr(services)


def test_service_attribute_access_errors_name_the_alternatives():
    with pytest.raises(AttributeError, match="No backend named 'nope'"):
        services.nope
    with pytest.raises(AttributeError):
        services._private
    with pytest.raises(AttributeError):
        ServiceCollection()._private


def test_service_handle_proxies_adapter_attributes_and_rejects_unknown():
    handle = services["tesseract"]
    with pytest.raises(AttributeError, match="has no attribute"):
        handle.definitely_not_there
    with pytest.raises(AttributeError):
        handle._private


# --- a REST adapter, no network ----------------------------------------------------------


def _fake_requests(monkeypatch, payload, calls):
    mod = types.ModuleType("requests")

    class Resp:
        def json(self):
            return payload

    def post(url, **kw):
        calls.append((url, kw))
        return Resp()

    mod.post = post
    monkeypatch.setitem(sys.modules, "requests", mod)


_OK = {
    "ParsedResults": [
        {
            "ParsedText": "hi there",
            "TextOverlay": {
                "Lines": [
                    {
                        "Words": [
                            {
                                "WordText": "hi",
                                "Left": 1,
                                "Top": 2,
                                "Width": 3,
                                "Height": 4,
                            }
                        ]
                    }
                ]
            },
        }
    ]
}


def test_ocr_space_posts_bytes_and_builds_word_blocks(monkeypatch):
    calls = []
    _fake_requests(monkeypatch, _OK, calls)
    result = ocracy.ocr(_png_bytes(), backend="ocr-space", api_key="k")
    assert result.text == "hi there"
    assert [b.text for b in result.words] == ["hi"]
    ((url, kw),) = calls
    assert "files" in kw and kw["data"]["apikey"] == "k"


def test_ocr_space_sends_urls_as_a_field_not_a_file(monkeypatch):
    calls = []
    _fake_requests(monkeypatch, _OK, calls)
    ocracy.ocr("https://x/i.png", backend="ocr-space", api_key="k")
    ((url, kw),) = calls
    assert kw["data"]["url"] == "https://x/i.png" and "files" not in kw


def test_ocr_space_processing_error_is_raised_with_its_message(monkeypatch):
    _fake_requests(
        monkeypatch, {"IsErroredOnProcessing": True, "ErrorMessage": "bad key"}, []
    )
    with pytest.raises(RuntimeError, match="OCR.space error: bad key"):
        ocracy.ocr(_png_bytes(), backend="ocr-space", api_key="k")
