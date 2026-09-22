# ocracy.backends.ocrmac.config

Configuration for the ocrmac backend (Apple Vision, macOS-only).

Wraps the on-device macOS Vision OCR. `languages` (ISO-639-1) is coerced to
Vision’s BCP-47 preference codes (`en` -> `en-US`). `recognition_level`
trades speed for accuracy (`"fast"` / `"accurate"`). Handwriting works
automatically. macOS only.
