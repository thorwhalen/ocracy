# ocracy.services

### ocracy.services *: [ServiceCollection](ocracy.html.md#ocracy.ServiceCollection)* *= <ServiceCollection backends=['aws-textract', 'azure-document-intelligence', 'claude-vision', 'easyocr', 'google-vision', 'gpt-4o-vision', 'mathpix', 'mistral-ocr', 'ocr-space', 'ocrmac', 'paddleocr', 'paddleocr-ppstructure', 'pix2tex-latex-ocr', 'rapidocr', 'tesseract', 'trocr-handwritten']>*

Lazy mapping of backend ids -> `ServiceHandle`.

Supports dict-style (`services['tesseract']`) and attribute-style
(`services.tesseract`) access.
