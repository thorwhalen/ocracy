"""Template backend — a copy-me starting point, NOT a real backend.

Its leading underscore makes the registry skip it. :func:`ocracy.make_backend.scaffold_backend`
reads ``config.py`` and ``adapter.py`` here, rewrites the lines marked
``# TEMPLATE`` with values from the ledger, and writes a new backend package.
"""
