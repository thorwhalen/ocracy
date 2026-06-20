"""Configuration for the Mathpix backend (Convert API).

The standard for STEM OCR: printed/handwritten math, chemistry, and tables into
LaTeX / Mathpix-Markdown. ``formats`` selects output formats. Needs BOTH
``MATHPIX_APP_ID`` and ``MATHPIX_APP_KEY`` (https://mathpix.com/ocr-api).
"""

BACKEND_CONFIG = {
    "id": "mathpix",
    "name": "mathpix",
    "display_name": "Mathpix (Convert API)",
    "pip_install": "requests",
    "import_name": "requests",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["math", "tables", "handwriting"],
    "default_for": [],
    "api_env_var": "MATHPIX_APP_KEY",
    "description": (
        "Best-in-class math/formula OCR — printed and handwritten equations, "
        "chemistry, and tables into LaTeX and Markdown."
    ),
    "param_map": {
        "formats": {"native_name": "formats", "default": ["text", "latex_styled"]},
    },
}
