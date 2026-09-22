# ocracy.base

Core types and normalized result objects for ocracy.

OCR engines disagree wildly on what they return: Tesseract emits TSV rows of
words with pixel boxes and confidences; cloud APIs return nested JSON of
pages/blocks/paragraphs/words; VLM-based engines often return just a Markdown
string. ocracy normalizes all of that into a small, stable set of dataclasses so
that callers get the *same shape* regardless of which backend produced the text:

- [`OcrResult`](#ocracy.base.OcrResult) — the full result of reading an image: a concatenated
  `text` (in reading order) plus a list of structured `blocks` carrying
  bounding boxes and confidences, plus the untouched `raw` backend output for
  power users who need engine-specific detail.
- [`TextBlock`](#ocracy.base.TextBlock) — one recognized unit of text (word/line/paragraph/block)
  with an optional [`BBox`](#ocracy.base.BBox) and `confidence`.
- [`BBox`](#ocracy.base.BBox) — an axis-aligned bounding box, with an optional `polygon` for
  rotated or quadrilateral regions (common in scene-text engines).

The input side is normalized too: every facade function accepts an
`ImageInput` — a path, URL, `bytes`, PIL image, or numpy array. Concrete
decoding happens lazily in [`ocracy.util`](ocracy.util.md#module-ocracy.util), so importing ocracy never
requires Pillow or numpy.

The design goal is *progressive disclosure*: `str(result)` gives you the text,
`result.text` is the same string, iterating the result yields its lines, and
`result.blocks` / `result.raw` are there when you need structure.

### Classes

| [`BBox`](#ocracy.base.BBox)(x0, y0, x1, y1[, polygon])                 | An axis-aligned bounding box in pixel coordinates (origin = top-left).   |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`OcrResult`](#ocracy.base.OcrResult)(text[, blocks, backend, raw, meta])   | The normalized result of reading an image with any backend.              |
| [`TextBlock`](#ocracy.base.TextBlock)(text[, bbox, confidence, level, ...]) | One recognized unit of text.                                             |

### *class* ocracy.base.BBox(x0, y0, x1, y1, polygon=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

An axis-aligned bounding box in pixel coordinates (origin = top-left).

`polygon` optionally carries the original (possibly rotated) vertices as a
sequence of `(x, y)` points; the axis-aligned `x0/y0/x1/y1` are always
populated (derived from the polygon if a backend only gives one).

#### *property* as_tuple *: [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple)[[float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float)]*

`(x0, y0, x1, y1)` — the convention PIL’s `crop` expects.

#### *classmethod* from_polygon(points)

Build a box from polygon vertices `[(x, y), ...]`.

The axis-aligned extent is computed from the vertices and the original
polygon is preserved for callers that care about rotation.

* **Return type:**
  [`BBox`](#ocracy.base.BBox)

#### *property* xywh *: [Tuple](https://docs.python.org/3/library/typing.html#typing.Tuple)[[float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float), [float](https://docs.python.org/3/builtins/functions.html#float)]*

`(x, y, width, height)` — the convention many drawing libs expect.

### *class* ocracy.base.OcrResult(text, blocks=<factory>, backend='', raw=None, meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The normalized result of reading an image with any backend.

`text` is the headline payload: the full recognized text in reading order.
`blocks` carries the structured units (with boxes/confidences) when the
backend provides them. `raw` is the untouched backend output. `meta`
holds cross-cutting extras (languages, page count, a Markdown rendering,
timing, …).

Progressive disclosure:

```default
result = ocracy.ocr("scan.png")
print(result)              # -> the text
result.text                # -> the same string
for line in result:        # -> iterate TextBlocks (lines by default)
    print(line.text, line.confidence)
result.words               # -> only word-level blocks
result.mean_confidence     # -> average confidence, if available
result.raw                 # -> engine-specific structure
```

#### at_level(level)

Blocks at a given granularity (`"word"`, `"line"`, …).

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`TextBlock`](#ocracy.base.TextBlock)]

#### filter_confidence(min_confidence)

Return a copy keeping only blocks at or above `min_confidence`.

Blocks without a confidence are dropped. `text` is rebuilt from the
surviving blocks (joined by newline).

* **Return type:**
  [`OcrResult`](#ocracy.base.OcrResult)

#### *classmethod* from_blocks(blocks, , backend='', raw=None, text=None, joiner='\\\\n', \*\*meta)

Build a result from structured blocks.

If `text` is not given it is synthesized by joining the blocks’ text in
their given order with `joiner` (callers should pass blocks already in
reading order, or pre-join and pass `text` explicitly).

* **Return type:**
  [`OcrResult`](#ocracy.base.OcrResult)

#### *classmethod* from_text(text, , backend='', raw=None, \*\*meta)

Build a minimal result from just a text string (no geometry).

* **Return type:**
  [`OcrResult`](#ocracy.base.OcrResult)

#### *property* markdown *: [str](https://docs.python.org/3/builtins/stdtypes.html#str) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Markdown rendering if the backend produced one (else `None`).

#### *property* mean_confidence *: [float](https://docs.python.org/3/builtins/functions.html#float) | [None](https://docs.python.org/3/builtins/constants.html#None)*

Mean confidence over blocks that report one, or `None`.

### *class* ocracy.base.TextBlock(text, bbox=None, confidence=None, level='line', language=None, meta=<factory>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One recognized unit of text.

#### text

The recognized string for this unit.

#### bbox

Where it was found (pixel coordinates), if the backend reports it.

#### confidence

Recognition confidence in `[0, 1]` (normalized by ocracy
from whatever scale the backend used), if available.

#### level

Granularity — one of `ocracy.base.LEVELS` (“word”, “line”, …).

#### language

Detected/declared language code for this unit, if any.

#### meta

Backend-specific extras (font size, style, page index, …).
