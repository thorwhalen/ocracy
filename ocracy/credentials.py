"""Credential resolution for remote OCR backends.

Remote engines need an API key (or a path to a service-account JSON). This module
holds ocracy's *data* -- which env vars each OCR provider uses and where to get a
key -- and binds it to the facade kit's chain (:mod:`ocracy.kit.credentials`):

1. an explicit value passed by the caller (``api_key=...``),
2. a key bound for the provider with :func:`using_credentials` (bring-your-own-key),
3. the backend's declared environment variable(s), then the provider's defaults,
4. (soft) a project ``.env`` found from the current directory, if ``python-dotenv``
   is installed,
5. (optional) an interactive prompt, only in a terminal and only if asked.

A backend declares its variable(s) in ``BACKEND_CONFIG['api_env_var']`` (a string
or list).
"""

from __future__ import annotations

from typing import Optional, Sequence, Union

from ocracy.kit import credentials as _kit
from ocracy.kit.credentials import (
    MissingCredentialError,
    current_credentials,
    using_credentials,
)

__all__ = [
    "resolve_credential",
    "credential_help",
    "using_credentials",
    "current_credentials",
    "PROVIDER_ENV_VARS",
    "CREDENTIAL_GUIDANCE",
    "MissingCredentialError",
]

#: Friendly provider -> canonical env-var name(s) for well-known services.
PROVIDER_ENV_VARS = {
    "google-vision": ["GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_API_KEY"],
    "google-document-ai": ["GOOGLE_APPLICATION_CREDENTIALS"],
    "aws-textract": ["AWS_ACCESS_KEY_ID"],  # plus AWS_SECRET_ACCESS_KEY / region
    "azure-vision": ["AZURE_VISION_KEY", "AZURE_COMPUTER_VISION_KEY"],
    "azure-document-intelligence": ["AZURE_DOCUMENT_INTELLIGENCE_KEY"],
    "ocr-space": ["OCR_SPACE_API_KEY"],
    "mathpix": ["MATHPIX_APP_KEY"],
    "mistral-ocr": ["MISTRAL_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "gemini": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
}


#: Where/how to get a key, per provider — powers the dynamic "missing credential"
#: errors AND the README. Keep links current; these are user-facing.
CREDENTIAL_GUIDANCE = {
    "google-vision": {
        "env_var": "GOOGLE_APPLICATION_CREDENTIALS",
        "get_key_url": "https://cloud.google.com/vision/docs/setup",
        "note": (
            "Create a Google Cloud project, enable the Cloud Vision API, create a "
            "service account, download its JSON key, and point "
            "GOOGLE_APPLICATION_CREDENTIALS at that file. Free tier: 1,000 units/month."
        ),
    },
    "ocr-space": {
        "env_var": "OCR_SPACE_API_KEY",
        "get_key_url": "https://ocr.space/ocrapi/freekey",
        "note": "Register a free API key by email; free tier allows 25,000 requests/month.",
    },
    "mathpix": {
        "env_var": "MATHPIX_APP_KEY (plus MATHPIX_APP_ID)",
        "get_key_url": "https://mathpix.com/ocr-api",
        "note": (
            "Create a Mathpix account, then copy your app_id and app_key from the "
            "Mathpix console; set MATHPIX_APP_ID and MATHPIX_APP_KEY."
        ),
    },
    "aws-textract": {
        "env_var": "AWS_ACCESS_KEY_ID (plus AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)",
        "get_key_url": "https://docs.aws.amazon.com/textract/latest/dg/getting-started.html",
        "note": "Create AWS credentials (IAM user/role) with Textract permissions.",
    },
    "azure-document-intelligence": {
        "env_var": "AZURE_DOCUMENT_INTELLIGENCE_KEY (plus AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT)",
        "get_key_url": "https://learn.microsoft.com/azure/ai-services/document-intelligence/create-document-intelligence-resource",
        "note": "Create a Document Intelligence resource in the Azure portal; copy its key and endpoint.",
    },
    "mistral-ocr": {
        "env_var": "MISTRAL_API_KEY",
        "get_key_url": "https://console.mistral.ai/api-keys",
        "note": "Create an API key in the Mistral console (La Plateforme).",
    },
    "openai": {
        "env_var": "OPENAI_API_KEY",
        "get_key_url": "https://platform.openai.com/api-keys",
        "note": "Create an API key in the OpenAI platform dashboard.",
    },
    "anthropic": {
        "env_var": "ANTHROPIC_API_KEY",
        "get_key_url": "https://console.anthropic.com/settings/keys",
        "note": "Create an API key in the Anthropic console.",
    },
    "gemini": {
        "env_var": "GOOGLE_API_KEY (or GEMINI_API_KEY)",
        "get_key_url": "https://aistudio.google.com/app/apikey",
        "note": "Create an API key in Google AI Studio.",
    },
}


def credential_help(provider: str) -> str:
    """A short, link-bearing 'how to get a key' message for ``provider`` (or '')."""
    return _kit.credential_help(provider, guidance=CREDENTIAL_GUIDANCE)


def resolve_credential(
    provider: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    env_var: Optional[Union[str, Sequence[str]]] = None,
    required: bool = True,
    prompt_if_missing: bool = False,
) -> Optional[str]:
    """Resolve a credential for a remote backend.

    Args:
        provider: A known provider id (see :data:`PROVIDER_ENV_VARS`) used to
            infer default env-var names, and the key for :func:`using_credentials`.
        api_key: An explicit value; if given, it wins and is returned as-is.
        env_var: Extra env-var name(s) to check (checked before provider defaults).
        required: If True (default), raise :class:`MissingCredentialError` when
            nothing resolves; if False, return ``None``.
        prompt_if_missing: If True and running interactively, prompt the user
            (via ``getpass``) as a last resort.

    Returns:
        The resolved secret, or ``None`` when ``required=False`` and nothing was
        found.
    """
    return _kit.resolve_credential(
        provider,
        api_key=api_key,
        env_var=env_var,
        provider_env_vars=PROVIDER_ENV_VARS,
        guidance=CREDENTIAL_GUIDANCE,
        dotenv=True,
        prompt_if_missing=prompt_if_missing,
        required=required,
    )
