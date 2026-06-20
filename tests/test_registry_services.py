"""Tests for backend discovery, the registry, and the service layer."""

import pytest

import ocracy
from ocracy import registry


def test_tesseract_is_discovered():
    backends = registry.list_backends()
    assert "tesseract" in backends


def test_template_is_not_discovered():
    # The _template package must be skipped by discovery.
    assert "_template" not in registry.list_backends()
    assert "__template__" not in registry.list_backends()


def test_get_config_without_loading_adapter():
    cfg = registry.get_config("tesseract")
    assert cfg["id"] == "tesseract"
    assert cfg["default_for"] == ["read"]
    assert "languages" in cfg["param_map"]


def test_default_backend_resolves():
    # Should resolve to some implemented backend (tesseract is the only one,
    # and it is default_for 'read').
    assert registry.get_default_backend("read") == "tesseract"


def test_services_attribute_and_dict_access():
    assert ocracy.services["tesseract"].name == "tesseract"
    assert ocracy.services.tesseract.info["id"] == "tesseract"
    with pytest.raises((KeyError, AttributeError)):
        _ = ocracy.services["does-not-exist"]


def test_unknown_backend_errors_are_friendly():
    with pytest.raises(KeyError):
        registry.get_config("nope")
