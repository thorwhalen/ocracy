"""Tests for the ledger (catalog) reading and filtering."""

import ocracy
from ocracy.catalog import BackendInfo, Catalog, catalog


def test_catalog_loads_and_is_mapping():
    assert len(catalog) > 5
    assert "tesseract" in catalog
    info = catalog["tesseract"]
    assert isinstance(info, BackendInfo)
    assert info.is_local is True
    assert info.is_remote is False
    assert info.pricing_model == "free_oss"  # via __getattr__ to the record


def test_implemented_flag_is_live():
    # The implemented set is computed from the registry, never stored — so it
    # equals exactly the backends that ship an adapter.
    from ocracy import registry

    impl = {i for i in catalog if catalog[i].implemented}
    assert impl == set(registry.list_backends())
    assert catalog["tesseract"].implemented is True
    # A ledger entry with no adapter package is listed-only, not implemented.
    assert catalog["abbyy-cloud-ocr"].implemented is False


def test_filter_composes_and_returns_catalog():
    local_oss = catalog.filter(is_local=True, open_source=True)
    assert isinstance(local_oss, Catalog)
    assert "tesseract" in local_oss
    assert "google-vision" not in local_oss

    remote = catalog.filter(is_remote=True)
    assert "google-vision" in remote
    assert "tesseract" not in remote


def test_filter_membership_value_list():
    excellent_or_good = catalog.filter(accuracy_tier={"excellent", "good"})
    assert "tesseract" in excellent_or_good


def test_supports_language_and_can_capability():
    fr = catalog.supports_language("French")
    # google-vision lists handwriting; tesseract does not
    hw = catalog.can("handwriting")
    assert "google-vision" in hw
    assert "tesseract" not in hw
    assert isinstance(fr, Catalog)


def test_find_shorthand_and_implemented_filter():
    impl = ocracy.find(implemented=True)
    assert "tesseract" in impl
    assert all(catalog[i].implemented for i in impl.ids)


def test_compare_view():
    rows = catalog.compare(["tesseract", "google-vision"], fields=["is_local", "pricing_model"])
    assert {r["id"] for r in rows} == {"tesseract", "google-vision"}
    by_id = {r["id"]: r for r in rows}
    assert by_id["tesseract"]["is_local"] is True
