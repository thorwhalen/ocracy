# PYTHON_ARGCOMPLETE_OK
"""ocracy command-line interface.

Exposes the tools in :mod:`ocracy.tools` as subcommands via ``cw``::

    ocracy read scan.png --backend tesseract --languages en,fr
    ocracy backends --capability math
    ocracy find --local --free --handwriting
    ocracy info google-vision
    ocracy scaffold surya
    ocracy validate tesseract

The CLI dependency (``cw``) is optional — ``import ocracy`` stays dependency-free.
Install it with ``pip install 'ocracy[cli]'``.

``cw.mk_parser`` returns a plain :class:`argparse.ArgumentParser`, and ``cw.run``
offers it to ``argcomplete`` before parsing, so the ``PYTHON_ARGCOMPLETE_OK`` marker
above keeps working with no adapter.
"""


def main() -> None:
    try:
        import cw
    except ImportError:  # pragma: no cover - exercised only without the extra
        import sys

        sys.exit(
            "The ocracy CLI requires 'cw'. Install it with: pip install 'ocracy[cli]'"
        )

    from ocracy.tools import _dispatch_funcs

    parser = cw.mk_parser(_dispatch_funcs)
    raise SystemExit(cw.run(parser))


if __name__ == "__main__":
    main()
