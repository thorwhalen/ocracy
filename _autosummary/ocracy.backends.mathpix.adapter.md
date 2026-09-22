# ocracy.backends.mathpix.adapter

Adapter for Mathpix — image -> Mathpix-Markdown / LaTeX via the Convert API.

Mathpix is a text-oriented (not box-oriented) engine: the primary payload is a
Markdown/LaTeX string, surfaced as `result.text` and `result.markdown`; the
LaTeX form and confidence are kept in `result.meta` and the raw JSON in
`result.raw`.

### Classes

| [`Adapter`](#ocracy.backends.mathpix.adapter.Adapter)(config)   | Mathpix Convert API adapter.   |
|--------------------------------------------------------------------|--------------------------------|

### *class* ocracy.backends.mathpix.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.md#ocracy.make_backend.BaseOcrAdapter)

Mathpix Convert API adapter.
