# ocracy.backends.aws_textract.config

Configuration for the AWS Textract backend.

This façade wraps Textract’s `detect_document_text` (text + word boxes +
confidence; handwriting included). Forms/tables/queries (`analyze_document`) are
a richer, pricier mode left for a future extension. Credentials use the standard
AWS chain (env vars, `~/.aws/credentials`, or an IAM role); set a region via
`region` or `AWS_DEFAULT_REGION`.
