"""Parameter translation between ocracy's normalized kwargs and native engines.

Every backend exposes its own parameter names and scales (``lang`` vs
``languages`` vs ``language_hints``; thresholds in ``0..1`` vs ``0..100``; pixel
vs point units). A backend declares a ``param_map`` in its ``BACKEND_CONFIG``
mapping *normalized* names to native ones, and :func:`make_kwargs_translator`
turns that declaration into a function that rewrites caller kwargs into the
shape the engine wants.

The machinery lives in the facade kit (:mod:`ocracy.kit.translation`), shared
with the fleet's other facades; this module keeps ocracy's original
``translate(**kwargs) -> dict`` shape for existing callers. New code that wants
the drops and clamps as notes uses :func:`ocracy.kit.make_translator` directly,
as :class:`~ocracy.make_backend.BaseOcrAdapter` does.
"""

from typing import Any, Callable, Dict, Optional

from ocracy.kit.translation import check_range, make_translator

__all__ = ["make_kwargs_translator", "validate_param"]


def make_kwargs_translator(
    param_map: Dict[str, Optional[dict]],
    *,
    on_unsupported: str = "warn",
) -> Callable[..., dict]:
    """Create a function that translates normalized kwargs to native kwargs.

    Args:
        param_map: Mapping of ``normalized_name -> spec``; see
            :mod:`ocracy.kit.translation` for every spec form (``None`` means the
            backend does not support the parameter).
        on_unsupported: ``"warn"`` (default), ``"raise"``, ``"note"`` or
            ``"ignore"``. The notes are discarded by this dict-returning form.

    Returns:
        A ``translate(**kwargs) -> dict`` function.
    """
    translator = make_translator(param_map, on_unsupported=on_unsupported)

    def translate(**kwargs) -> dict:
        return translator(kwargs).kwargs

    return translate


def validate_param(name: str, value: Any, config: dict) -> Any:
    """Validate a single parameter against ``min``/``max``/``choices`` in config."""
    return check_range(name, value, config)
