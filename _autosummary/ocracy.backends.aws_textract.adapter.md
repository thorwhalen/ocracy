# ocracy.backends.aws_textract.adapter

Adapter for AWS Textract — image -> text + word boxes via detect_document_text.

Textract reports geometry as fractions of the page (0..1), so this adapter scales
boxes to pixels using the decoded image size. LINE blocks build the reading-order
text; WORD blocks carry boxes + confidence (rescaled 0..100 -> 0..1).

### Classes

| [`Adapter`](#ocracy.backends.aws_textract.adapter.Adapter)(config)   | AWS Textract adapter.   |
|--------------------------------------------------------------------|-------------------------|

### *class* ocracy.backends.aws_textract.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.md#ocracy.make_backend.BaseOcrAdapter)

AWS Textract adapter.
