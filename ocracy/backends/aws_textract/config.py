"""Configuration for the AWS Textract backend.

This façade wraps Textract's ``detect_document_text`` (text + word boxes +
confidence; handwriting included). Forms/tables/queries (``analyze_document``) are
a richer, pricier mode left for a future extension. Credentials use the standard
AWS chain (env vars, ``~/.aws/credentials``, or an IAM role); set a region via
``region`` or ``AWS_DEFAULT_REGION``.
"""

BACKEND_CONFIG = {
    "id": "aws-textract",
    "name": "aws-textract",
    "display_name": "AWS Textract",
    "pip_install": "boto3",
    "import_name": "boto3",
    "license": "proprietary",
    "is_local": False,
    "is_remote": True,
    "capabilities": ["handwriting"],
    "default_for": [],
    "api_env_var": "AWS_ACCESS_KEY_ID",
    "description": (
        "Cloud OCR for business documents with handwriting; word boxes + "
        "confidence. (Forms/tables available in Textract's analyze mode.)"
    ),
    "param_map": {
        "region": {"native_name": "region_name"},
    },
}
