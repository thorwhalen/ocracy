# ocracy.backends.pix2tex_latex_ocr.config

Configuration for the pix2tex (LaTeX-OCR) backend.

Local, offline math OCR: turns an image of a (typically single) printed equation
into LaTeX — the free, self-hosted counterpart to Mathpix. The LaTeX string is
returned as `result.text` and also wrapped as `result.markdown` (`$$…$$`).
Heavy (PyTorch); first run downloads model weights.
