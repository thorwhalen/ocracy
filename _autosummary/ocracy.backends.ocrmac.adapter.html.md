# ocracy.backends.ocrmac.adapter

Adapter for ocrmac — image -> text via the macOS Vision framework.

Vision reports bounding boxes as normalized `(x, y, w, h)` with a bottom-left
origin; this adapter converts them to ocracy’s pixel, top-left convention using
the image’s pixel size.

### Classes

| [`Adapter`](#ocracy.backends.ocrmac.adapter.Adapter)(config)   | Apple Vision adapter (macOS only).   |
|--------------------------------------------------------------------|--------------------------------------|

### *class* ocracy.backends.ocrmac.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

Apple Vision adapter (macOS only).
