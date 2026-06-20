"""Configuration for the Template backend (copy-me).

``scaffold_backend`` rewrites the lines tagged ``# TEMPLATE`` from a ledger entry.
Everything else you fill in by hand: the ``param_map`` is where you map ocracy's
normalized argument names (``languages``, ``detect_orientation``, ...) onto the
engine's native parameter names. See ``ocracy/data/SCHEMA.md`` for field meanings.
"""

BACKEND_CONFIG = {
    "id": "__template__",  # TEMPLATE
    "name": "__template__",  # TEMPLATE
    "display_name": "Template Backend",  # TEMPLATE
    "pip_install": "PACKAGE",  # TEMPLATE  e.g. "pytesseract Pillow"
    "import_name": "PACKAGE",  # TEMPLATE  module used to probe availability
    "license": "unknown",  # TEMPLATE
    "is_local": False,  # TEMPLATE
    "is_remote": False,  # TEMPLATE
    # Capabilities BEYOND the implied primary "read" (image -> text):
    # e.g. "tables", "math", "handwriting", "layout", "barcodes".
    "capabilities": [],
    # Capabilities this backend should be the *default* for (usually ["read"]
    # for your first/most general engine).
    "default_for": [],
    # For remote backends: the env var(s) holding the credential, else "".
    "api_env_var": "",
    "description": "One-line description of the engine.",  # TEMPLATE
    # Map normalized kwarg -> native kwarg config (or None if unsupported):
    #   {"native_name": "lang", "default": "eng", "coerce": <callable>}
    "param_map": {
        "languages": {"native_name": "lang"},
    },
}
