"""Credential resolution for remote OCR backends.

Remote engines need an API key (or a path to a service-account JSON). Rather than
make each adapter reinvent the lookup, this module centralizes a small, layered
resolver:

1. an explicit value passed by the caller (``api_key=...``),
2. the backend's declared environment variable(s),
3. (soft) a ``.env`` file discovered via ``python-dotenv`` if it is installed,
4. (optional) an interactive prompt, only in a REPL and only if asked.

A backend declares its variable(s) in ``BACKEND_CONFIG['api_env_var']`` (a string
or list). The well-known providers below give friendly defaults. The design
follows the credential pattern used by the sibling ``aix`` facade.
"""

from __future__ import annotations

import os
import sys
from typing import List, Optional, Sequence, Union

__all__ = [
    "resolve_credential",
    "credential_help",
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
    g = CREDENTIAL_GUIDANCE.get(provider)
    if not g:
        return ""
    return (
        f"How to get a credential for {provider}: {g['note']} "
        f"Get a key: {g['get_key_url']}"
    )


class MissingCredentialError(RuntimeError):
    """Raised when a required credential cannot be resolved.

    Its message includes provider-specific, link-bearing guidance on how to
    obtain a key (see :data:`CREDENTIAL_GUIDANCE`).
    """


def _candidate_env_vars(
    provider: Optional[str], env_var: Optional[Union[str, Sequence[str]]]
) -> List[str]:
    names: List[str] = []
    if env_var:
        names.extend([env_var] if isinstance(env_var, str) else list(env_var))
    if provider and provider in PROVIDER_ENV_VARS:
        names.extend(PROVIDER_ENV_VARS[provider])
    # De-dup preserving order.
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _soft_load_dotenv() -> None:
    """Load a ``.env`` into the environment if python-dotenv is available."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return
    load_dotenv()


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
            infer default env-var names.
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
    if api_key:
        return api_key

    candidates = _candidate_env_vars(provider, env_var)

    for name in candidates:
        val = os.environ.get(name)
        if val:
            return val

    # Soft .env discovery, then re-check.
    _soft_load_dotenv()
    for name in candidates:
        val = os.environ.get(name)
        if val:
            return val

    if prompt_if_missing and sys.stdin is not None and sys.stdin.isatty():
        import getpass

        label = candidates[0] if candidates else (provider or "API key")
        val = getpass.getpass(f"Enter credential for {label}: ").strip()
        if val:
            if candidates:
                os.environ[candidates[0]] = val
            return val

    if required:
        hint = f" (set one of: {', '.join(candidates)})" if candidates else ""
        guidance = credential_help(provider) if provider else ""
        msg = f"No credential found for {provider or 'backend'}{hint}."
        if guidance:
            msg += "\n" + guidance
        raise MissingCredentialError(msg)
    return None
