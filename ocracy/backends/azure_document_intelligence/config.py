"""Configuration for the Azure AI Document Intelligence backend.

``model`` selects the analysis model: ``prebuilt-read`` (default; text + words +
handwriting) or ``prebuilt-layout`` (adds reading order, tables, and structure).
Needs both a key (``AZURE_DOCUMENT_INTELLIGENCE_KEY``) and an endpoint
(``AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT``, or pass ``endpoint=``).
"""

BACKEND_CONFIG = {
    "id": "azure-document-intelligence",
    "name": "azure-document-intelligence",
    "display_name": "Azure AI Document Intelligence",
    "pip_install": "azure-ai-documentintelligence",
    "import_name": "azure.ai.documentintelligence",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["handwriting", "layout", "tables"],
    "default_for": [],
    "api_env_var": "AZURE_DOCUMENT_INTELLIGENCE_KEY",
    "description": (
        "Top-tier document AI: text + handwriting in 100+ languages, with reading "
        "order, tables, and Markdown via the layout model. On-prem container option."
    ),
    "param_map": {
        "model": {"native_name": "model_id", "default": "prebuilt-read"},
        "endpoint": {"native_name": "endpoint"},
    },
}
