"""Configuration for the pix2tex (LaTeX-OCR) backend.

Local, offline math OCR: turns an image of a (typically single) printed equation
into LaTeX — the free, self-hosted counterpart to Mathpix. The LaTeX string is
returned as ``result.text`` and also wrapped as ``result.markdown`` (``$$…$$``).
Heavy (PyTorch); first run downloads model weights.
"""

BACKEND_CONFIG = {
    "id": "pix2tex-latex-ocr",
    "name": "pix2tex-latex-ocr",
    "display_name": "pix2tex (LaTeX-OCR)",
    "pip_install": "pix2tex",
    "import_name": "pix2tex",
    "license": "MIT",
    "is_local": True,
    "is_remote": False,
    "capabilities": ["math"],
    "default_for": [],
    "api_env_var": "",
    "description": (
        "Local, offline math/equation image -> LaTeX (the free counterpart to "
        "Mathpix). Best on a single printed formula at a time."
    ),
    "param_map": {},
}
