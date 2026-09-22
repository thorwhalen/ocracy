# ocracy.credentials

Credential resolution for remote OCR backends.

Remote engines need an API key (or a path to a service-account JSON). Rather than
make each adapter reinvent the lookup, this module centralizes a small, layered
resolver:

1. an explicit value passed by the caller (`api_key=...`),
2. the backend’s declared environment variable(s),
3. (soft) a `.env` file discovered via `python-dotenv` if it is installed,
4. (optional) an interactive prompt, only in a REPL and only if asked.

A backend declares its variable(s) in `BACKEND_CONFIG['api_env_var']` (a string
or list). The well-known providers below give friendly defaults. The design
follows the credential pattern used by the sibling `aix` facade.

### Module Attributes

| [`PROVIDER_ENV_VARS`](#ocracy.credentials.PROVIDER_ENV_VARS)   | Friendly provider -> canonical env-var name(s) for well-known services.                               |
|----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------|
| [`CREDENTIAL_GUIDANCE`](#ocracy.credentials.CREDENTIAL_GUIDANCE) | Where/how to get a key, per provider — powers the dynamic "missing credential" errors AND the README. |

### Functions

| [`resolve_credential`](#ocracy.credentials.resolve_credential)([provider, api_key, ...])   | Resolve a credential for a remote backend.                               |
|-------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`credential_help`](#ocracy.credentials.credential_help)(provider)                      | A short, link-bearing 'how to get a key' message for `provider` (or ''). |

### Exceptions

| [`MissingCredentialError`](#ocracy.credentials.MissingCredentialError)   | Raised when a required credential cannot be resolved.   |
|---------------------------------------------------------------------------|---------------------------------------------------------|

### ocracy.credentials.CREDENTIAL_GUIDANCE *= {'anthropic': {'env_var': 'ANTHROPIC_API_KEY', 'get_key_url': 'https://console.anthropic.com/settings/keys', 'note': 'Create an API key in the Anthropic console.'}, 'aws-textract': {'env_var': 'AWS_ACCESS_KEY_ID (plus AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION)', 'get_key_url': 'https://docs.aws.amazon.com/textract/latest/dg/getting-started.html', 'note': 'Create AWS credentials (IAM user/role) with Textract permissions.'}, 'azure-document-intelligence': {'env_var': 'AZURE_DOCUMENT_INTELLIGENCE_KEY (plus AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT)', 'get_key_url': 'https://learn.microsoft.com/azure/ai-services/document-intelligence/create-document-intelligence-resource', 'note': 'Create a Document Intelligence resource in the Azure portal; copy its key and endpoint.'}, 'gemini': {'env_var': 'GOOGLE_API_KEY (or GEMINI_API_KEY)', 'get_key_url': 'https://aistudio.google.com/app/apikey', 'note': 'Create an API key in Google AI Studio.'}, 'google-vision': {'env_var': 'GOOGLE_APPLICATION_CREDENTIALS', 'get_key_url': 'https://cloud.google.com/vision/docs/setup', 'note': 'Create a Google Cloud project, enable the Cloud Vision API, create a service account, download its JSON key, and point GOOGLE_APPLICATION_CREDENTIALS at that file. Free tier: 1,000 units/month.'}, 'mathpix': {'env_var': 'MATHPIX_APP_KEY (plus MATHPIX_APP_ID)', 'get_key_url': 'https://mathpix.com/ocr-api', 'note': 'Create a Mathpix account, then copy your app_id and app_key from the Mathpix console; set MATHPIX_APP_ID and MATHPIX_APP_KEY.'}, 'mistral-ocr': {'env_var': 'MISTRAL_API_KEY', 'get_key_url': 'https://console.mistral.ai/api-keys', 'note': 'Create an API key in the Mistral console (La Plateforme).'}, 'ocr-space': {'env_var': 'OCR_SPACE_API_KEY', 'get_key_url': 'https://ocr.space/ocrapi/freekey', 'note': 'Register a free API key by email; free tier allows 25,000 requests/month.'}, 'openai': {'env_var': 'OPENAI_API_KEY', 'get_key_url': 'https://platform.openai.com/api-keys', 'note': 'Create an API key in the OpenAI platform dashboard.'}}*

Where/how to get a key, per provider — powers the dynamic “missing credential”
errors AND the README. Keep links current; these are user-facing.

### *exception* ocracy.credentials.MissingCredentialError

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

Raised when a required credential cannot be resolved.

Its message includes provider-specific, link-bearing guidance on how to
obtain a key (see [`CREDENTIAL_GUIDANCE`](#ocracy.credentials.CREDENTIAL_GUIDANCE)).

### ocracy.credentials.PROVIDER_ENV_VARS *= {'anthropic': ['ANTHROPIC_API_KEY'], 'aws-textract': ['AWS_ACCESS_KEY_ID'], 'azure-document-intelligence': ['AZURE_DOCUMENT_INTELLIGENCE_KEY'], 'azure-vision': ['AZURE_VISION_KEY', 'AZURE_COMPUTER_VISION_KEY'], 'gemini': ['GOOGLE_API_KEY', 'GEMINI_API_KEY'], 'google-document-ai': ['GOOGLE_APPLICATION_CREDENTIALS'], 'google-vision': ['GOOGLE_APPLICATION_CREDENTIALS', 'GOOGLE_API_KEY'], 'mathpix': ['MATHPIX_APP_KEY'], 'mistral-ocr': ['MISTRAL_API_KEY'], 'ocr-space': ['OCR_SPACE_API_KEY'], 'openai': ['OPENAI_API_KEY']}*

Friendly provider -> canonical env-var name(s) for well-known services.

### ocracy.credentials.credential_help(provider)

A short, link-bearing ‘how to get a key’ message for `provider` (or ‘’).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### ocracy.credentials.resolve_credential(provider=None, , api_key=None, env_var=None, required=True, prompt_if_missing=False)

Resolve a credential for a remote backend.

* **Parameters:**
  * **provider** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – A known provider id (see [`PROVIDER_ENV_VARS`](#ocracy.credentials.PROVIDER_ENV_VARS)) used to
    infer default env-var names.
  * **api_key** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – An explicit value; if given, it wins and is returned as-is.
  * **env_var** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Extra env-var name(s) to check (checked before provider defaults).
  * **required** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True (default), raise [`MissingCredentialError`](#ocracy.credentials.MissingCredentialError) when
    nothing resolves; if False, return `None`.
  * **prompt_if_missing** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True and running interactively, prompt the user
    (via `getpass`) as a last resort.
* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  The resolved secret, or `None` when `required=False` and nothing was
  found.
