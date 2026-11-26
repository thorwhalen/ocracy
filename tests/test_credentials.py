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


# --- declared credentials (the ocracy.credentials.v1 entry-point contract) ------


def _install_fake_dist(tmp_path, monkeypatch, module_source, target="fake_creds:ROWS"):
    import importlib
    import sys

    from ocracy.kit.credentials import CREDENTIALS_ENTRY_POINT_GROUP

    site = tmp_path / "site"
    info = site / "fakecreds-0.1.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Metadata-Version: 2.1\nName: fakecreds\nVersion: 0.1\n")
    (info / "entry_points.txt").write_text(
        f"[{CREDENTIALS_ENTRY_POINT_GROUP}]\nfakecreds = {target}\n"
    )
    (site / "fake_creds.py").write_text(module_source)
    monkeypatch.syspath_prepend(str(site))
    sys.modules.pop("fake_creds", None)
    importlib.invalidate_caches()


def _fake_rows(rows, problems):
    return [r for r in rows if r["package"] == "fakecreds"], [
        p for p in problems if p.startswith("fakecreds")
    ]


def test_read_declared_credentials_reads_lists_and_callables(tmp_path, monkeypatch):
    from ocracy.kit.credentials import read_declared_credentials

    _install_fake_dist(
        tmp_path,
        monkeypatch,
        "def ROWS():\n    return [{'provider': 'acme', 'env_vars': 'ACME_KEY', 'cost': 'cheap'}]\n",
    )
    rows, problems = _fake_rows(*read_declared_credentials())
    assert rows == [
        {"provider": "acme", "env_vars": ["ACME_KEY"], "cost": "cheap", "package": "fakecreds"}
    ]
    assert problems == []


def test_a_broken_declaration_is_a_problem_not_an_exception(tmp_path, monkeypatch):
    from ocracy.kit.credentials import read_declared_credentials

    _install_fake_dist(tmp_path, monkeypatch, "ROWS = [{'provider': 'acme'}]\n")
    rows, problems = _fake_rows(*read_declared_credentials())
    assert rows == [] and problems and "ValueError" in problems[0]


def test_ocracy_declares_its_own_credentials_from_its_tables():
    from ocracy.credentials import (
        CREDENTIAL_GUIDANCE,
        PROVIDER_ENV_VARS,
        declared_credentials,
    )
    from ocracy.kit.credentials import normalize_credential_row

    rows = declared_credentials()
    assert {r["provider"] for r in rows} == set(PROVIDER_ENV_VARS)
    for row in rows:
        assert normalize_credential_row(row) == row
        assert row["env_vars"] == list(dict.fromkeys(PROVIDER_ENV_VARS[row["provider"]]))
        url = (CREDENTIAL_GUIDANCE.get(row["provider"]) or {}).get("get_key_url")
        assert row.get("get_key_url") == url


def test_credential_rows_skips_providers_with_no_env_var_and_dedupes():
    from ocracy.kit.credentials import credential_rows

    assert credential_rows({"a": ["A", "A", "B"], "b": None, "c": []}) == [
        {"provider": "a", "env_vars": ["A", "B"]}
    ]


@pytest.mark.parametrize(
    "row",
    [
        "not a mapping",
        {"env_vars": ["A"]},
        {"provider": "p", "env_vars": []},
        {"provider": "p", "env_vars": ["A", ""]},
        {"provider": "p", "env_vars": ["A"], "note": 3},
        {"provider": "p", "env_vars": ["A"], "note": 0},
        {"provider": "p", "env_vars": ["A"], "cost": False},
        {"provider": "p", "env_vars": ["A"], "also_requires": [""]},
        {"provider": "p", "env_vars": ["A"], "also_requires": 3},
    ],
)
def test_normalize_refuses_malformed_rows(row):
    from ocracy.kit.credentials import normalize_credential_row

    with pytest.raises(ValueError):
        normalize_credential_row(row)


def test_declared_rows_carry_the_variables_a_provider_needs_together():
    from ocracy.credentials import declared_credentials

    rows = {r["provider"]: r for r in declared_credentials()}
    assert rows["mathpix"]["also_requires"] == ["MATHPIX_APP_ID"]
    assert rows["aws-textract"]["also_requires"] == ["AWS_SECRET_ACCESS_KEY"]
    assert rows["azure-document-intelligence"]["also_requires"] == [
        "AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT"
    ]
    assert "also_requires" not in rows["openai"]


def test_also_requires_is_normalized_and_an_older_reader_may_drop_it():
    from ocracy.kit.credentials import normalize_credential_row

    row = {"provider": "p", "env_vars": "A", "also_requires": "B"}
    assert normalize_credential_row(row)["also_requires"] == ["B"]
    assert "also_requires" not in normalize_credential_row(
        {"provider": "p", "env_vars": "A", "also_requires": []}
    )
