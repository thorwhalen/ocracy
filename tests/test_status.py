"""Tests for the readiness-status helpers (no OCR / no network: run_tests=False)."""

import ocracy
from ocracy.status import LEVELS


def test_levels_are_nested():
    all_ids = set(ocracy.backend_ids("all"))
    impl = set(ocracy.backend_ids("implemented"))
    assert impl <= all_ids
    assert len(all_ids) >= len(impl) >= 1
    assert "tesseract" in impl


def test_backend_info_has_level_flags_and_website():
    info = ocracy.backend_info(run_tests=False)
    assert set(info) == set(ocracy.backend_ids("all"))
    for d in info.values():
        assert "implemented" in d and "set_up" in d and "tested" in d
        assert "website" in d
        assert d["tested"] is None  # run_tests=False => not attempted
    # set_up implies implemented; nothing is tested when run_tests=False
    for i, d in info.items():
        if d["set_up"]:
            assert d["implemented"]


def test_backend_ids_from_info_is_consistent():
    info = ocracy.backend_info(run_tests=False)
    assert ocracy.backend_ids("implemented", info=info) == sorted(
        i for i, d in info.items() if d["implemented"]
    )
    assert ocracy.backend_ids("tested", info=info) == []  # none tested


def test_status_table_is_aligned_markdown():
    info = ocracy.backend_info(run_tests=False)
    table = ocracy.status_table(info=info)
    lines = table.splitlines()
    assert lines[0].startswith("| Name")
    assert set(lines[1]) <= set("| -")  # separator row
    assert len(lines) == len(info) + 2  # header + separator + one row per backend


def test_names_with_sites_format():
    s = ocracy.names_with_sites(["tesseract"])
    assert s.startswith("Tesseract") and "(http" in s


def test_levels_constant():
    assert LEVELS == ("all", "implemented", "set_up", "tested")
