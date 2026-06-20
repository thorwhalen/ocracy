"""Adapter for AWS Textract — image -> text + word boxes via detect_document_text.

Textract reports geometry as fractions of the page (0..1), so this adapter scales
boxes to pixels using the decoded image size. LINE blocks build the reading-order
text; WORD blocks carry boxes + confidence (rescaled 0..100 -> 0..1).
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """AWS Textract adapter."""

    def _read(self, image, *, region_name=None, **extra) -> OcrResult:
        import boto3
        from botocore.exceptions import NoCredentialsError, PartialCredentialsError

        from ocracy.credentials import MissingCredentialError, credential_help
        from ocracy.util import load_image_bytes, to_pil

        data = load_image_bytes(image)
        try:
            client = boto3.client("textract", region_name=region_name)
            response = client.detect_document_text(Document={"Bytes": data})
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise MissingCredentialError(
                "AWS credentials not found.\n" + credential_help("aws-textract")
            ) from e

        width, height = to_pil(data).size  # reuse decoded bytes (no refetch)

        lines, blocks = [], []
        for b in response.get("Blocks", []):
            kind = b.get("BlockType")
            if kind == "LINE":
                lines.append(b.get("Text", ""))
            elif kind == "WORD":
                bb = b.get("Geometry", {}).get("BoundingBox", {})
                x0 = bb.get("Left", 0) * width
                y0 = bb.get("Top", 0) * height
                x1 = x0 + bb.get("Width", 0) * width
                y1 = y0 + bb.get("Height", 0) * height
                blocks.append(
                    make_block(
                        b.get("Text", ""),
                        bbox=(x0, y0, x1, y1),
                        confidence=b.get("Confidence"),
                        conf_scale=100,
                        level="word",
                    )
                )

        return OcrResult.from_blocks(
            blocks, backend=self.backend_id, raw=response, text="\n".join(lines)
        )
