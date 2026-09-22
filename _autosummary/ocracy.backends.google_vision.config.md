# ocracy.backends.google_vision.config

Configuration for the Google Cloud Vision backend.

`languages` (ISO-639-1) maps to Vision `language_hints`. `document=True`
(default) uses DOCUMENT_TEXT_DETECTION (dense text + handwriting + structure);
`document=False` uses TEXT_DETECTION (sparse/scene text). Auth is Google ADC —
set `GOOGLE_APPLICATION_CREDENTIALS` to a service-account JSON
([https://cloud.google.com/vision/docs/setup](https://cloud.google.com/vision/docs/setup)).
