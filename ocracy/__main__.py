# PYTHON_ARGCOMPLETE_OK
"""ocracy command-line interface.

Exposes the tools in :mod:`ocracy.tools` as subcommands via ``argh``::

    ocracy read scan.png --backend tesseract --languages en,fr
    ocracy backends --capability math
    ocracy find --local --free --handwriting
    ocracy info google-vision
    ocracy scaffold surya
    ocracy validate tesseract

The CLI dependency (``argh``) is optional — ``import ocracy`` stays dependency-free.
Install it with ``pip install 'ocracy[cli]'``.
"""


def main() -> None:
    try:
        import argh
    except ImportError:  # pragma: no cover - exercised only without the extra
        import sys

        sys.exit(
            "The ocracy CLI requires 'argh'. Install it with: pip install 'ocracy[cli]'"
        )

    from ocracy.tools import _dispatch_funcs

    parser = argh.ArghParser()
    parser.add_commands(_dispatch_funcs)

    try:  # optional shell tab-completion
        import argcomplete

        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    parser.dispatch()


if __name__ == "__main__":
    main()
