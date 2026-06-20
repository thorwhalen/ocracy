"""Adapter for Google Cloud Vision — image -> text + word boxes + confidence."""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """Google Cloud Vision adapter (caches the client)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            from ocracy.credentials import MissingCredentialError, credential_help

            try:
                from google.cloud import vision

                self._client = vision.ImageAnnotatorClient()
            except Exception as e:  # DefaultCredentialsError and friends
                if "default credentials" in str(e).lower() or "credential" in str(e).lower():
                    raise MissingCredentialError(
                        "Google Cloud Vision could not find credentials.\n"
                        + credential_help("google-vision")
                    ) from e
                raise
        return self._client

    def _read(self, image, *, language_hints=None, document=True, **extra) -> OcrResult:
        from google.cloud import vision

        from ocracy.util import load_image_bytes

        client = self._get_client()
        content = load_image_bytes(image)
        vimage = vision.Image(content=content)
        ctx = vision.ImageContext(language_hints=language_hints) if language_hints else None

        if document:
            response = client.document_text_detection(image=vimage, image_context=ctx)
        else:
            response = client.text_detection(image=vimage, image_context=ctx)

        if response.error.message:
            raise RuntimeError(f"Google Vision error: {response.error.message}")

        fta = response.full_text_annotation
        text = fta.text if fta and fta.text else ""

        blocks = []
        for page in (fta.pages if fta else []):
            for block in page.blocks:
                for para in block.paragraphs:
                    for word in para.words:
                        wtext = "".join(sym.text for sym in word.symbols)
                        verts = [(v.x, v.y) for v in word.bounding_box.vertices]
                        conf = getattr(word, "confidence", None)
                        blocks.append(
                            make_block(
                                wtext,
                                bbox=verts if len(verts) >= 3 else None,
                                confidence=conf,
                                level="word",
                            )
                        )

        # If detection returned only text_annotations (sparse mode), fall back.
        if not text and response.text_annotations:
            text = response.text_annotations[0].description

        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=response, text=text)
