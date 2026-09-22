# ocracy.backends.tesseract.config

Configuration for the Tesseract backend.

Demonstrates the `param_map` pattern: ocracy’s normalized `languages` (a list
of ISO-639-1 codes like `["en", "fr"]`) is coerced to Tesseract’s native
`lang` string (`"eng+fra"`). `psm` / `oem` / `config` are passed through
and assembled into a Tesseract config string by the adapter.
