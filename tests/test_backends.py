"""Tests for the concrete backend façades.

The structural tests (config integrity, parameter translation) run with no engine
installed — they exercise ocracy's wiring, not the engines. The end-to-end checks
are skipped automatically when an engine's dependency is missing.
"""

import pytest

import ocracy
from ocracy import registry
from ocracy.make_backend import validate_adapter

IMPLEMENTED = [
    "tesseract", "easyocr", "rapidocr", "paddleocr", "ocrmac",
    "pix2tex-latex-ocr", "trocr-handwritten",
    "ocr-space", "google-vision", "mistral-ocr", "mathpix",
    "aws-textract", "azure-document-intelligence",
    "claude-vision", "gpt-4o-vision",
]
LOCAL = ["tesseract", "easyocr", "rapidocr", "paddleocr", "ocrmac"]


@pytest.mark.parametrize("bid", IMPLEMENTED)
def test_config_integrity(bid):
    c = registry.get_config(bid)
    assert c["id"] == bid
    assert c["import_name"]  # availability probe target
    assert isinstance(c["is_local"], bool) and isinstance(c["is_remote"], bool)
    assert c["is_local"] != c["is_remote"]  # exactly one is true for our picks
    if c["is_remote"]:
        assert c["api_env_var"], f"{bid} is remote but declares no api_env_var"


def test_param_translation_without_engines():
    # Each adapter can be constructed (no engine import) and translate kwargs.
    from ocracy.backends.easyocr.adapter import Adapter as Easy
    from ocracy.backends.easyocr.config import BACKEND_CONFIG as easy_cfg
    from ocracy.backends.ocr_space.adapter import Adapter as Space
    from ocracy.backends.ocr_space.config import BACKEND_CONFIG as space_cfg

    a = Easy(easy_cfg)
    assert a._translate(languages=["en", "zh"]) == {"lang_list": ["en", "ch_sim"], "gpu": False}

    s = Space(space_cfg)
    native = s._translate(languages=["fr"], ocr_engine=2)
    assert native["language"] == "fre"
    assert native["OCREngine"] == 2
    assert native["isOverlayRequired"] is True  # default injected


def test_language_coercions():
    from ocracy.backends.ocrmac.config import _to_vision_langs
    from ocracy.backends.tesseract.config import _to_tess_lang

    assert _to_tess_lang(["en", "fr"]) == "eng+fra"
    assert _to_tess_lang("eng") == "eng"
    assert _to_tess_lang(None) is None
    assert _to_vision_langs(["en", "fr"]) == ["en-US", "fr-FR"]
    assert _to_vision_langs(["en-GB"]) == ["en-GB"]  # already BCP-47 -> passthrough


@pytest.mark.parametrize("bid", LOCAL)
def test_local_backend_end_to_end_if_available(bid):
    report = validate_adapter(bid)
    if not report.get("available"):
        pytest.skip(f"{bid} engine not installed")
    assert report["ran"], report.get("error")
    assert report["returns_ocrresult"]


def test_remote_backend_missing_credentials_is_helpful(monkeypatch):
    # With no key in the environment, calling a remote backend raises a
    # MissingCredentialError whose message includes a 'get a key' link.
    from ocracy.credentials import MissingCredentialError

    for var in ("OCR_SPACE_API_KEY",):
        monkeypatch.delenv(var, raising=False)
    img = b"not-a-real-image"  # never reached; credential check happens first
    with pytest.raises(MissingCredentialError) as ei:
        ocracy.services["ocr-space"].read(img)
    assert "ocr.space" in str(ei.value).lower()  # the signup link
