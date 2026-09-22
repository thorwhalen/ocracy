# ocracy.backends.azure_document_intelligence.adapter

Adapter for Azure AI Document Intelligence — image -> text + word polygons.

Uses the analyze-document API; `result.content` is the full text and each
page’s words carry a polygon and confidence. Requires a key and an endpoint.

### Classes

| [`Adapter`](#ocracy.backends.azure_document_intelligence.adapter.Adapter)(config)   | Azure Document Intelligence adapter.   |
|--------------------------------------------------------------------|----------------------------------------|

### *class* ocracy.backends.azure_document_intelligence.adapter.Adapter(config)

Bases: [`BaseOcrAdapter`](ocracy.make_backend.md#ocracy.make_backend.BaseOcrAdapter)

Azure Document Intelligence adapter.
