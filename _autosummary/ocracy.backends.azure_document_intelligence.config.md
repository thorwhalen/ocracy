# ocracy.backends.azure_document_intelligence.config

Configuration for the Azure AI Document Intelligence backend.

`model` selects the analysis model: `prebuilt-read` (default; text + words +
handwriting) or `prebuilt-layout` (adds reading order, tables, and structure).
Needs both a key (`AZURE_DOCUMENT_INTELLIGENCE_KEY`) and an endpoint
(`AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`, or pass `endpoint=`).
