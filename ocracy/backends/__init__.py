"""Implemented OCR backends.

Each real backend is a subpackage with a ``config.py`` (``BACKEND_CONFIG``) and an
``adapter.py`` (``Adapter`` with a ``read`` method). The registry
(:mod:`ocracy.registry`) discovers them automatically. Subpackages whose name
starts with ``_`` (e.g. :mod:`ocracy.backends._template`) are scaffolding
helpers, not real backends, and are skipped by discovery.

To add a backend, scaffold one from the template::

    from ocracy.make_backend import scaffold_backend
    scaffold_backend("easyocr")   # creates ocracy/backends/easyocr/ from the template
"""
