---
name: ocracy-install-backend
description: >-
  Install / set up an ocracy OCR backend that isn't available yet — handle the
  heavy or awkward installs (PaddleOCR's framework, Torch-based EasyOCR/TrOCR/
  pix2tex, Tesseract's *system* binary, GPU vs CPU wheels, first-run model-weight
  downloads, remote-API credentials). Use when ocracy raises "Backend X requires:
  pip install ...", an `ImportError` for an OCR engine, when the user says
  "install <engine> for ocracy", "set up paddleocr/easyocr/tesseract", "make this
  OCR backend work", "ocracy backend not installed", or "which OCR backends do I
  have installed". Drives `ocracy.requirements()`, `ocracy.check()`,
  `ocracy.doctor()`, and `ocracy.install()`. To *pick* a backend first see
  ocracy-choose-backend; to *use* one see ocracy.
---

# Installing an ocracy backend

`import ocracy` is dependency-free; each engine is an optional extra, and some
need more than a `pip install` (a system binary, a GPU wheel, model weights, or a
credential). ocracy turns those into structured, OS-aware steps you can act on.

## 1. See what's installed (and what isn't)

```python
import ocracy
ocracy.check("paddleocr")     # -> True/False: usable right now? (no network)
ocracy.doctor()               # -> {"available": [...], "missing": {id: hint}}
```
Shell: `ocracy doctor`.

## 2. Get the exact requirements for a backend

```python
req = ocracy.requirements("paddleocr")     # or ocracy.requirements("easyocr", gpu=True)
print(req.instructions())                   # copy-pasteable plan
req.pip_command      # 'pip install "ocracy[paddleocr]"'
req.system           # OS-specific system-dep commands for THIS machine (e.g. tesseract)
req.gpu              # GPU-wheel guidance, if any
req.weights          # first-run model-download note, if any
req.alternative      # a lighter backend with comparable results, if any
req.credentials      # for remote backends: env var(s) + where to get a key
```
Shell: `ocracy requirements paddleocr` (add `--gpu`).

## 3. Install it

**Run the pip step.** Either let ocracy do it, or run the printed command yourself:

```python
ocracy.install("rapidocr", yes=True)        # runs pip in the current interpreter, then verifies
# yes=False (default) is a dry run: returns the plan, changes nothing
```
Shell: `ocracy install rapidocr --yes` (omit `--yes` for a dry run).

**Handle the parts pip can't do** (ocracy surfaces these; run them yourself, with
the user's OK):

- **System binary** (e.g. Tesseract): run `req.system` — `brew install tesseract`
  (macOS) / `sudo apt-get install -y tesseract-ocr` (Linux). The pip wrapper alone
  won't work without it.
- **GPU**: the default install is CPU. For GPU, follow `req.gpu` (e.g.
  `pip install paddlepaddle-gpu`, or a CUDA build of Torch from pytorch.org) —
  CUDA-version-specific, so don't guess; surface it to the user.
- **Model weights**: heavy engines download weights on first `ocr()` call
  (`req.weights` says where) — the first run is slow, not broken.
- **Credentials** (remote backends): no package needed beyond a small client;
  set the env var from `req.credentials` (it includes the signup link).

## 4. Verify

```python
ocracy.check("rapidocr")                    # True once installed
ocracy.validate_adapter("rapidocr")         # end-to-end smoke test on a generated image
```

## Tips for tricky ones

- **PaddleOCR** install fighting you? Use **`rapidocr`** — same PP-OCR models via
  ONNX, no PaddlePaddle framework, CPU-only, trivial install. `req.alternative`
  flags this automatically.
- **EasyOCR / TrOCR / pix2tex** pull PyTorch (large) and download weights — expect
  a multi-hundred-MB first install; on a CPU box they work but are slow.
- **ocrmac** is macOS-only (built-in Apple Vision; nothing to install but the
  wrapper).
- **No GPU + want frontier accuracy + no ops?** Don't fight a local GPU engine —
  use a remote one (`google-vision`, `mistral-ocr`); `ocracy.requirements(id)`
  shows the credential to set instead.

The full per-engine recipes live in `ocracy/install.py`; the backend's own
`pip_install` and `import_name` are in its `config.py`.
