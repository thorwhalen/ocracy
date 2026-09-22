"""Both `LEVELS` tuples must be reachable, unambiguously, from the package root.

`ocracy.base.LEVELS` (OCR granularity) and `ocracy.status.LEVELS` (backend
readiness) are two different tuples that used to collide at the package root:
the `ocracy.status` import shadowed the `ocracy.base` one, so the granularity
tuple was unreachable from `ocracy` and `__all__` listed "LEVELS" twice. These
tests pin the disambiguated names AND pin the value of the existing public
`ocracy.LEVELS` so it can never be silently rebound again.
"""

import ocracy
import ocracy.base
import ocracy.status


GRANULARITY = ("page", "block", "paragraph", "line", "word", "char")
READINESS = ("all", "implemented", "set_up", "tested")


def test_granularity_levels_reachable_from_package_root():
    assert ocracy.GRANULARITY_LEVELS == GRANULARITY
    assert ocracy.GRANULARITY_LEVELS is ocracy.base.LEVELS


def test_status_levels_reachable_from_package_root():
    assert ocracy.STATUS_LEVELS == READINESS
    assert ocracy.STATUS_LEVELS is ocracy.status.LEVELS


def test_public_levels_still_means_readiness():
    """Back-compat pin: `ocracy.LEVELS` keeps the readiness meaning it has today."""
    assert ocracy.LEVELS == READINESS
    assert ocracy.LEVELS is ocracy.status.LEVELS


def test_all_has_no_duplicates():
    assert len(ocracy.__all__) == len(set(ocracy.__all__))


def test_all_names_are_exported():
    missing = sorted(set(ocracy.__all__) - set(dir(ocracy)))
    assert not missing, f"__all__ names not present on the package: {missing}"
