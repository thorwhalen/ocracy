"""Adapter for the Template backend (copy-me).

An adapter turns ocracy's normalized request into a native engine call and the
native response into an :class:`ocracy.base.OcrResult`. Subclassing
:class:`ocracy.make_backend.BaseOcrAdapter` gives you kwarg translation for free:
implement :meth:`_read`, which receives the image and the already-translated
*native* kwargs, and return an ``OcrResult``.

Three jobs in ``_read``:

1. Get the image into the form the engine wants
   (``ocracy.util.ensure_file_path`` / ``load_image_bytes`` / ``to_pil``).
2. Call the engine (import it *inside* ``_read`` so importing ocracy stays light).
3. Normalize the output — use ``ocracy.make_backend.make_block`` /
   ``OcrResult.from_blocks`` / ``OcrResult.from_text``, and stash the engine's
   native response in ``raw=``.
"""

from ocracy.base import OcrResult  # noqa: F401  (commonly needed)
from ocracy.make_backend import BaseOcrAdapter, make_block  # noqa: F401


class Adapter(BaseOcrAdapter):
    """Template adapter — replace the body of ``_read``."""

    def _read(self, image, **native_kwargs) -> OcrResult:
        # 1. import the engine here (lazy)
        # import the_engine
        #
        # 2. normalize the input and call the engine
        # from ocracy.util import ensure_file_path, cleanup_temp
        # path, is_temp = ensure_file_path(image)
        # try:
        #     native = the_engine.run(path, **native_kwargs)
        # finally:
        #     cleanup_temp(path, is_temp)
        #
        # 3. build a normalized result
        # blocks = [make_block(w.text, bbox=..., conf=w.score) for w in native.words]
        # return OcrResult.from_blocks(blocks, backend=self.backend_id, raw=native)
        raise NotImplementedError("Implement _read for this backend.")
