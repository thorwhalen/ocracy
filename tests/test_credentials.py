"""Tests for credential resolution and the link-bearing guidance."""

import pytest

from ocracy.credentials import (
    CREDENTIAL_GUIDANCE,
    MissingCredentialError,
    credential_help,
    resolve_credential,
)


def test_explicit_api_key_wins():
    assert resolve_credential("ocr-space", api_key="explicit") == "explicit"


def test_env_var_resolution(monkeypatch):
    monkeypatch.setenv("OCR_SPACE_API_KEY", "from-env")
    assert resolve_credential("ocr-space") == "from-env"


def test_missing_required_raises_with_link(monkeypatch):
    monkeypatch.delenv("OCR_SPACE_API_KEY", raising=False)
    monkeypatch.delenv("MATHPIX_APP_KEY", raising=False)
    with pytest.raises(MissingCredentialError) as ei:
        resolve_credential("mathpix")
    msg = str(ei.value)
    assert "MATHPIX_APP_KEY" in msg
    assert CREDENTIAL_GUIDANCE["mathpix"]["get_key_url"] in msg


def test_not_required_returns_none(monkeypatch):
    monkeypatch.delenv("OCR_SPACE_API_KEY", raising=False)
    assert resolve_credential("ocr-space", required=False) is None


def test_credential_help_has_link_for_known_providers():
    for provider, g in CREDENTIAL_GUIDANCE.items():
        help_str = credential_help(provider)
        assert g["get_key_url"] in help_str
    assert credential_help("unknown-provider") == ""
