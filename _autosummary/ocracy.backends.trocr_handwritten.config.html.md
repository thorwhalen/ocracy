# ocracy.backends.trocr_handwritten.config

Configuration for the TrOCR (handwritten) backend.

Local, offline handwriting recognition via HuggingFace TrOCR transformer models.

#### NOTE
TrOCR recognizes a single text line per image — for full pages, segment into
line crops upstream and call once per line. Heavy (PyTorch + transformers); first
run downloads the model. `model_name` selects the checkpoint.
