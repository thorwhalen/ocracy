# ocracy.backends.pix2tex_latex_ocr.adapter

Adapter for pix2tex — image of an equation -> LaTeX, locally.

Math OCR is text-oriented: the LaTeX string is `result.text`, also surfaced as
`result.markdown` (`$$…$$`) and `result.meta['latex']`. The model is heavy to
construct, so it is built once and cached.

### Classes

| [`Adapter`](#ocracy.backends.pix2tex_latex_ocr.adapter.Adapter)(config)   | pix2tex (LaTeX-OCR) adapter (caches the model).   |
|--------------------------------------------------------------------|---------------------------------------------------|

### *class* ocracy.backends.pix2tex_latex_ocr.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.html.md#ocracy.make_backend.BaseOcrAdapter)

pix2tex (LaTeX-OCR) adapter (caches the model).
