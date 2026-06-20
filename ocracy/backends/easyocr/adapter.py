"""Adapter for EasyOCR — image -> text + polygon boxes via easyocr.Reader."""

from ocracy.base import OcrResult
from ocracy.make_backend import BaseOcrAdapter, make_block


class Adapter(BaseOcrAdapter):
    """EasyOCR adapter (caches one Reader per language-set + gpu flag)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._readers: dict = {}

    def _reader(self, langs, gpu):
        key = (tuple(langs), bool(gpu))
        if key not in self._readers:
            import easyocr

            self._readers[key] = easyocr.Reader(list(langs), gpu=bool(gpu))
        return self._readers[key]

    def _read(self, image, *, lang_list=None, gpu=False, **extra) -> OcrResult:
        from ocracy.util import to_numpy

        langs = lang_list or ["en"]
        reader = self._reader(langs, gpu)
        arr = to_numpy(image)
        # readtext -> list of (polygon[[x,y]*4], text, confidence)
        results = reader.readtext(arr, **extra)
        blocks = [
            make_block(text, bbox=poly, confidence=float(conf), level="line")
            for poly, text, conf in results
        ]
        return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=results)
