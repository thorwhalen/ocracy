"""Adapter for TrOCR (handwritten) — image of a text line -> text, locally.

Loads a HuggingFace ``VisionEncoderDecoderModel`` + ``TrOCRProcessor`` (cached per
checkpoint) and decodes one line of (hand)written text. TrOCR is line-level: the
recognized line is ``result.text``.
"""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter


class Adapter(BaseOcrAdapter):
    """TrOCR adapter (caches the processor + model per checkpoint)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._processor = None
        self._model = None
        self._loaded = None

    def _load(self, model_name):
        if self._loaded != model_name:
            import os

            # TrOCR is a PyTorch model. Force transformers to its torch backend so
            # it doesn't import an (often stale, NumPy-1.x-compiled) TensorFlow/Flax
            # just for backend detection — a common cause of import-time failures.
            os.environ.setdefault("USE_TF", "0")
            os.environ.setdefault("USE_FLAX", "0")

            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            self._processor = TrOCRProcessor.from_pretrained(model_name)
            self._model = VisionEncoderDecoderModel.from_pretrained(model_name)
            self._loaded = model_name
        return self._processor, self._model

    def _read(
        self, image, *, model_name="microsoft/trocr-base-handwritten", **extra
    ) -> OcrResult:
        from ocracy.util import to_pil

        processor, model = self._load(model_name)
        pil = to_pil(image).convert("RGB")
        pixel_values = processor(images=pil, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return OcrResult.from_text(
            text,
            backend=self.backend_id,
            raw={"model_name": model_name},
            model=model_name,
        )
