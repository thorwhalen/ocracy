"""Adapter for Azure AI Document Intelligence — image -> text + word polygons.

Uses the analyze-document API; ``result.content`` is the full text and each
page's words carry a polygon and confidence. Requires a key and an endpoint.
"""

import os

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """Azure Document Intelligence adapter."""

    def _read(self, image, *, model_id="prebuilt-read", endpoint=None, **extra) -> OcrResult:
        # Resolve credentials first (cheap, dependency-free) so missing key/endpoint
        # fails fast with guidance before we import the SDK / network.
        from ocracy.credentials import (
            MissingCredentialError,
            credential_help,
            resolve_credential,
        )

        key = resolve_credential(
            "azure-document-intelligence",
            api_key=extra.pop("api_key", None),
            env_var=self.config.get("api_env_var"),
        )
        endpoint = endpoint or os.environ.get("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT")
        if not endpoint:
            raise MissingCredentialError(
                "Azure Document Intelligence needs an endpoint "
                "(AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT).\n"
                + credential_help("azure-document-intelligence")
            )

        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential

        from ocracy.util import load_image_bytes

        data = load_image_bytes(image)
        client = DocumentIntelligenceClient(endpoint, AzureKeyCredential(key))
        poller = client.begin_analyze_document(
            model_id, body=data, content_type="application/octet-stream"
        )
        result = poller.result()

        text = getattr(result, "content", "") or ""
        blocks = []
        for page in getattr(result, "pages", None) or []:
            for word in getattr(page, "words", None) or []:
                poly = getattr(word, "polygon", None)
                bbox = None
                if poly and len(poly) >= 8:
                    bbox = [(poly[i], poly[i + 1]) for i in range(0, len(poly), 2)]
                blocks.append(
                    make_block(
                        getattr(word, "content", ""),
                        bbox=bbox,
                        confidence=getattr(word, "confidence", None),
                        level="word",
                    )
                )

        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=result, text=text)
