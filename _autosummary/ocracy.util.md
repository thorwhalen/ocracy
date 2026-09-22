# ocracy.util

Image-input normalization and small shared helpers.

Different OCR backends want their input in different forms: a filesystem path
(Tesseract, PaddleOCR), raw `bytes` (most cloud REST APIs), a PIL image, or a
numpy array (deep-learning engines). Callers, meanwhile, want to pass whatever
they have — a path, an `http(s)` URL, bytes, a PIL image, or an array. This
module bridges the two with a handful of converters that **lazily** import
Pillow / numpy / urllib only when actually exercised, so `import ocracy` stays
dependency-free.

The key converters:

- [`load_image_bytes()`](#ocracy.util.load_image_bytes) — anything -> encoded image `bytes` (for REST APIs).
- [`ensure_file_path()`](#ocracy.util.ensure_file_path) — anything -> a path on disk (writing a temp file for
  in-memory inputs); pair with [`cleanup_temp()`](#ocracy.util.cleanup_temp) or use [`image_path()`](#ocracy.util.image_path).
- [`image_path()`](#ocracy.util.image_path) — a context manager yielding a path and cleaning up.
- [`to_pil()`](#ocracy.util.to_pil) / [`to_numpy()`](#ocracy.util.to_numpy) — anything -> a PIL image / numpy array.

### Functions

| [`classify_input`](#ocracy.util.classify_input)(image)                              | Classify an image input as `url`/`path`/`bytes`/`pil`/`numpy`.                                                          |
|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| [`is_url`](#ocracy.util.is_url)(x)                                          | True if `x` is a string that looks like an http(s) URL.                                                                 |
| [`load_image_bytes`](#ocracy.util.load_image_bytes)(image, \*[, fmt])                 | Return encoded image `bytes` for any supported input.                                                                   |
| [`ensure_file_path`](#ocracy.util.ensure_file_path)(image, \*[, suffix])              | Return `(path, is_temp)` for any supported input.                                                                       |
| [`cleanup_temp`](#ocracy.util.cleanup_temp)(path, is_temp)                        | Delete `path` iff `is_temp` (the flag returned by [`ensure_file_path()`](#ocracy.util.ensure_file_path)). |
| [`image_path`](#ocracy.util.image_path)(image, \*[, suffix])                    | Context manager yielding a filesystem path for `image`, cleaning up temps.                                              |
| [`to_pil`](#ocracy.util.to_pil)(image)                                      | Convert any supported input into a PIL `Image` (lazy import).                                                           |
| [`to_numpy`](#ocracy.util.to_numpy)(image)                                    | Convert any supported input into a numpy array (lazy import).                                                           |
| [`check_import`](#ocracy.util.check_import)(module_name, \*, install_hint[, ...]) | Import `module_name` or raise a friendly, actionable ImportError.                                                       |

### ocracy.util.check_import(module_name, , install_hint, feature='this')

Import `module_name` or raise a friendly, actionable ImportError.

Centralizes the “you need to `pip install X`” guidance so adapters and
converters don’t each hand-roll it.

### ocracy.util.classify_input(image)

Classify an image input as `url`/`path`/`bytes`/`pil`/`numpy`.

Decided structurally (and via duck typing for PIL/numpy) so we never import
Pillow or numpy just to look at the input.

* **Return type:**
  str

### ocracy.util.cleanup_temp(path, is_temp)

Delete `path` iff `is_temp` (the flag returned by [`ensure_file_path()`](#ocracy.util.ensure_file_path)).

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### ocracy.util.ensure_file_path(image, , suffix='.png')

Return `(path, is_temp)` for any supported input.

Existing on-disk paths are returned untouched (`is_temp=False`). In-memory
inputs (bytes/URL/PIL/numpy) are written to a temp file (`is_temp=True`);
the caller is responsible for cleanup (use [`cleanup_temp()`](#ocracy.util.cleanup_temp), or prefer
the [`image_path()`](#ocracy.util.image_path) context manager).

* **Return type:**
  Tuple[str, bool]

### ocracy.util.image_path(image, , suffix='.png')

Context manager yielding a filesystem path for `image`, cleaning up temps.

Example:

```default
with image_path(pil_image) as p:
    text = pytesseract.image_to_string(p)
```

* **Return type:**
  Iterator[str]

### ocracy.util.is_url(x)

True if `x` is a string that looks like an http(s) URL.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### ocracy.util.load_image_bytes(image, , fmt='PNG')

Return encoded image `bytes` for any supported input.

Pass-through for `bytes`; reads files; fetches URLs; encodes PIL/numpy
inputs as `fmt` (PNG by default — lossless and universally accepted).

* **Return type:**
  bytes

### ocracy.util.to_numpy(image)

Convert any supported input into a numpy array (lazy import).

### ocracy.util.to_pil(image)

Convert any supported input into a PIL `Image` (lazy import).
