# The OCR Landscape — Engines, Services & Build-vs-Wrap Analysis

> Decision-grade research report for the `ocracy` facade package. Produced by the
> `ocr-landscape-research` multi-agent workflow (106 candidates surveyed → 64
> deep-dived → adversarially fact-checked). **As-of 2026-06.** The structured data
> behind every table is the ledger `ocracy/data/backends.json` (browse via
> `ocracy.catalog`); per-engine citations live in each ledger record.

---

## 1. Executive summary

1. **Build a fresh, thin facade — do not wrap an existing aggregator.** The candidate "facades" each carry a worldview that conflicts with `ocracy`'s goal of *one uniform call over heterogeneous backends*. `pyocr` is unmaintained and narrow; **RapidOCR** is a single-engine deployment shell (ONNX PaddleOCR), not a multi-backend facade; **Surya**, **docling**, and **unstructured** are document-ETL/parsing pipelines whose object model (typed document elements, chunking, Markdown ETL) is heavier and more opinionated than a `text + boxes + confidence` result type. The closest precedents — `owocr` and `img2table` — *are* multi-backend dispatchers, and they validate the pattern (`owocr` already unifies ~15 local + cloud engines behind one CLI), but both are domain-scoped (Japanese on-screen text; tables). The right move is the `denote`/`aix` sibling pattern already scaffolded: a normalized `OcrResult`, a data-driven ledger, lazy per-backend extras, and a scaffold workflow. Wrap *engines*, not *another facade*.

2. **A normalized result type is feasible across the whole field, but two capabilities resist normalization.** Almost every backend yields text + word/line bounding boxes + per-element confidence (Tesseract, EasyOCR, docTR, cloud APIs). Two axes break the lowest common denominator: (a) **bounding boxes/confidence vanish in VLM/LLM OCR** (GPT-4o, Claude, Nougat, GOT-OCR2.0 expose neither natively); (b) **"beyond-text" output** (Markdown, LaTeX math, HTML tables) is structured, not a flat string. `ocracy`'s `result.markdown` / `result.raw` escape hatches already account for this; treat boxes/confidence as `Optional`.

3. **The local/open-source tier is strong enough that most users never need a paid API.** For commodity printed text, **PaddleOCR (PP-OCRv5/v6)** and **RapidOCR** give near-SOTA accuracy on CPU, Apache-2.0, 100+ languages, with tables/math/handwriting in the VL variant. **Tesseract** remains the zero-friction baseline. The paid tier earns its keep only for (a) managed scale without GPU ops, (b) turnkey structured extraction (invoices/IDs), or (c) frontier handwriting/multilingual where you lack a GPU.

4. **VLM OCR has overtaken specialized engines on document-parsing benchmarks but is the wrong default.** On OmniDocBench v1.5/v1.6, PaddleOCR-VL (~96%), dots.ocr, DeepSeek-OCR, and MinerU lead, beating GPT-4o and Gemini on text/tables/reading-order. But VLMs hallucinate, lack boxes/confidence, need a GPU, and bill per token. Keep them as *opt-in power backends*, not the facade default.

5. **Pricing clusters into three bands.** Commodity cloud OCR ≈ **$1.50/1,000 pages**; VLM-OCR APIs are cheaper still — **Mistral OCR $2/1k (→$1 batch)**, self-hosted olmOCR **~$0.0002/page**; structured IDP is far pricier — **AWS Forms $50/1k, Forms+Tables+Queries $70/1k**, Google Form Parser **$30/1k**. Self-hosted OSS is free + your compute.

6. **Recommended first-implementation shortlist (10 backends).** Local+free: `tesseract`, `paddleocr`, `easyocr`, `rapidocr`, `ocrmac`. Remote+paid: `google-vision`, `azure-document-intelligence` (or `aws-textract`), `mistral-ocr`. Beyond-text: `mathpix` and/or `pix2tex`, plus Wave-2 `trocr-handwritten`/`surya`. Guarantees ≥4 local, ≥3 remote, ≥4 free, ≥3 paid, and covers math/tables/handwriting.

7. **Leave the long tail in the ledger, unimplemented but discoverable** — legacy engines (OCRopus, MMOCR, keras-ocr), niche SaaS (Veryfi, Taggun, Klippa), and the heavy VLM zoo. The live-computed `implemented` flag keeps the catalog honest.

8. **The ledger schema is the product's moat** — the decision layer (`find`, `can`, `supports_language`, `compare`) is the real differentiator vs. any single engine. Keep fields dated; the field churns monthly.

---

## 2. What features matter for choosing an OCR backend

*(Each axis is a ledger column because it changes a build-or-buy decision.)*

- **Local vs. remote** — the most consequential axis (privacy/air-gap/compute vs. zero-ops scale/frontier models); several backends are both (PaddleOCR, MinerU, Surya, Qwen-VL, dots.ocr, Nanonets, Mistral).
- **Pricing model** — five regimes: free_oss, freemium, free_tier_then_paid, pay_as_you_go, proprietary_quote; normalize to per-1,000-pages.
- **Accuracy** — three frames: CER/WER (line recognition), OmniDocBench/OCRBench (full-page), table TEDS/olmOCR-bench (structure); flag vendor-vs-independent.
- **Language/script coverage** — English-only to 200+; script families matter more than counts; handwriting coverage is a narrower subset.
- **Handwriting, Math, Tables, Layout/reading-order, Output formats, Bounding boxes & confidence** (absent in most generative VLMs → keep `Optional`), **Privacy, GPU, Maturity** (guards against shipping over a dead engine).

---

## 3. Category deep-dives

Covers (a) local/OSS general engines (Tesseract baseline; PaddleOCR standout; EasyOCR/RapidOCR/docTR/OnnxTR/ocrmac/winocr; Kraken/Calamari/OCR4all for historical HTR), (b) cloud OCR & document-AI APIs (Google/Azure/AWS "big three" at ~$1.50/1k; Document AI / IDP tier; receipt specialists), (c) LLM/VLM OCR (self-hostable open-weight VLMs now lead OmniDocBench; hosted frontier VLMs excel at understanding but hallucinate; Mistral as the pragmatic VLM-OCR API), (d) specialized math/tables/handwriting/receipts (Mathpix, pix2tex, TATR, img2table, Camelot, TrOCR-handwritten), and (e) the **build-vs-wrap evidence**: only `owocr` and `img2table` are honest multi-backend dispatchers (both domain-scoped, GPL), the rest are single-engine shells or document-ETL pipelines → **build fresh**.

> Note: the narrative above consolidates per-engine sources; the **References**
> section lists the primary sources gathered across all 64 ledger records. The
> comparison tables below are generated directly from the ledger for completeness.

## 4. Comparison tables

Generated from the ledger (40 local engines, 24 pure-remote services). Legend:
✓ yes · ~ limited · ✗ no · ? unknown. "Langs" = documented language count.

### 4a. Local / self-hostable engines

| Engine | License | Pricing | Accuracy | Langs | Hand | Math | Tables | Best for |
|---|---|---|---|---|---|---|---|---|
| Calamari OCR (`calamari`) | GPL-3.0-or-later | Free (OSS) | excellent | — | ~ | ✗ | ✗ | Digital-humanities and library/archive projects doing high-… |
| DeepSeek-OCR (`deepseek-ocr`) | MIT | Free (OSS) | excellent | 100 | ~ | ✓ | ✓ | Large-scale, GPU-backed document-to-markdown/text conversio… |
| InternVL (3 / 3.5) (`internvl`) | Apache-2.0 (Int… | Free (OSS) | excellent | — | ~ | ✓ | ✓ | Self-hosted, privacy-sensitive document/chart/screenshot un… |
| Marker (Datalab) (`marker`) | GPL-3.0-or-late… | Mixed | excellent | 90 | ✓ | ✓ | ✓ | Converting whole PDFs and office/EPUB documents to clean Ma… |
| Microsoft Table Transformer (TATR) (`table-transformer`) | MIT | Free (OSS) | excellent | — | ✗ | ✗ | ✓ | Detecting tables and recovering their cell/row/column struc… |
| MinerU (`mineru`) | MinerU Open Sou… | Freemium | excellent | 109 | ~ | ✓ | ✓ | Converting complex PDFs, scanned documents, and Office file… |
| MiniCPM-V (4.5 / 4.6) (`minicpm-v`) | Apache-2.0 | Free (OSS) | excellent | 30 | ✓ | ✓ | ✓ | On-device / privacy-sensitive document OCR and document und… |
| Nanonets (`nanonets`) | mixed (propriet… | Freemium | excellent | 12 | ✓ | ✓ | ✓ | Teams needing no-code/low-code IDP for invoices, receipts, … |
| OCR4all (`ocr4all`) | MIT | Free (OSS) | excellent | — | ✓ | ✗ | ~ | Libraries, archives, and digital-humanities researchers doi… |
| PaddleOCR (PP-OCRv5 / PaddleOCR-V… (`paddleocr`) | Apache-2.0 | Free (OSS) | excellent | 109 | ✓ | ✓ | ✓ | High-accuracy multilingual document parsing and OCR where y… |
| PaddleOCR 3.0 / PP-StructureV3 (`paddleocr-ppstructure`) | Apache-2.0 | Free (OSS) | excellent | 109 | ~ | ✓ | ✓ | Self-hosted, free, high-accuracy parsing of complex multi-c… |
| Qwen2-VL / Qwen2.5-VL / Qwen3-VL (`qwen-vl`) | Apache-2.0 (ope… | Mixed | excellent | 32 | ✓ | ✓ | ✓ | Complex multilingual document parsing where layout, tables,… |
| Texify / Surya (LaTeX OCR) (`texify-surya`) | Apache-2.0 (Sur… | Free tier+paid | excellent | 91 | ~ | ✓ | ✓ | Converting math/equation images and PDFs to MathJax/KaTeX-r… |
| TrOCR (`trocr`) | MIT | Free (OSS) | excellent | — | ✓ | ✗ | ✗ | Recognizing the text content of pre-cropped single text-lin… |
| TrOCR (handwritten) (`trocr-handwritten`) | MIT (source/bas… | Free (OSS) | excellent | — | ✓ | ✗ | ✗ | High-accuracy recognition of English handwritten (cursive i… |
| dots.ocr (`dots-ocr`) | MIT | Free (OSS) | excellent | 100 | ~ | ✓ | ✓ | Self-hosted, cost-free, privacy-preserving end-to-end docum… |
| olmOCR (`olmocr`) | Apache-2.0 | Free (OSS) | excellent | 1 | ✓ | ✓ | ✓ | Large-scale, cost-efficient linearization of English PDFs (… |
| Azure AI Vision Read OCR (Compute… (`azure-ai-vision-read`) | proprietary | Free tier+paid | good | 164 | ✓ | ✗ | ~ | Cloud applications already on Azure that need reliable prin… |
| Docling (`docling`) | MIT | Free (OSS) | good | 80 | ~ | ✓ | ✓ | Self-hosted, privacy-sensitive document-to-structured-conte… |
| EasyOCR (`easyocr`) | Apache-2.0 | Free (OSS) | good | 86 | ~ | ✗ | ✗ | Local, offline, multilingual extraction of text + bounding … |
| GOT-OCR2.0 (`got-ocr2`) | Apache-2.0 (cod… | Free (OSS) | good | — | ~ | ✓ | ✓ | Teams needing a free, self-hosted, privacy-preserving singl… |
| Kraken (`kraken`) | Apache-2.0 | Free (OSS) | good | — | ✓ | ✗ | ~ | Digitizing historical manuscripts and early printed books, … |
| Llama 3.2 Vision (11B / 90B) (`llama-3-2-vision`) | LLAMA-3.2-COMMU… | Mixed | good | 8 | ~ | ~ | ✓ | Teams that want an open-weight, self-hostable multimodal mo… |
| MMOCR (`mmocr`) | Apache-2.0 | Free (OSS) | good | — | ~ | ✗ | ✗ | Researchers and ML engineers who want to train, fine-tune, … |
| Nougat (`nougat`) | MIT (code); mod… | Free (OSS) | good | — | ✗ | ✓ | ✓ | Converting born-digital or scanned English scientific/acade… |
| OCRopus / ocropy (`ocropus`) | Apache-2.0 | Free (OSS) | good | — | ~ | ✗ | ✗ | Historical and early-printed-book OCR pipelines where you t… |
| OnnxTR (`onnxtr`) | Apache-2.0 | Free (OSS) | good | 100 | ✗ | ✗ | ✗ | Production OCR on printed/scanned documents where you want … |
| RapidOCR (`rapidocr`) | Apache-2.0 | Free (OSS) | good | 12 | ~ | ✗ | ~ | Fast, fully offline, privacy-preserving multilingual OCR (e… |
| Surya OCR (`surya`) | Apache-2.0 (cod… | Freemium | good | 91 | ~ | ✓ | ✓ | Self-hosted, multilingual document OCR with built-in layout… |
| Tesseract (pytesseract / tesseroc… (`tesseract`) | Apache-2.0 | Free (OSS) | good | 116 | ✗ | ✗ | ~ | Local, free, offline OCR of clean printed/typed documents i… |
| Unstructured.io API (`unstructured-io`) | Apache-2.0 (cor… | Free tier+paid | good | — | ~ | ✓ | ✓ | RAG/LLM ingestion pipelines that need to turn heterogeneous… |
| docTR (`doctr`) | Apache-2.0 | Free (OSS) | good | — | ~ | ✗ | ~ | Developers needing a free, self-hosted, privacy-preserving … |
| ocrmac (Apple Vision) (`ocrmac`) | MIT | Free (OSS) | good | 18 | ~ | ✗ | ✗ | Fast, free, fully on-device OCR of printed text from images… |
| pix2tex / LaTeX-OCR (`pix2tex-latex-ocr`) | MIT | Free (OSS) | good | — | ~ | ✓ | ✗ | Turning images/screenshots of a single printed mathematical… |
| Keras-OCR (`keras-ocr`) | MIT | Free (OSS) | fair | 1 | ✗ | ✗ | ✗ | Self-hosted, free English scene/printed-text detection+reco… |
| winocr (Windows OCR) (`winocr`) | MIT (the Python… | Free (OSS) | fair | 25 | ✗ | ✗ | ✗ | Windows-only pipelines needing free, fully offline OCR of c… |
| Camelot (`camelot`) | MIT | Free (OSS) | varies | — | ✗ | ✗ | ✓ | Extracting tabular data from born-digital, text-based PDFs … |
| Tabula / tabula-py (`tabula-py`) | MIT | Free (OSS) | varies | — | ✗ | ✗ | ✓ | Extracting tabular data from text-based (digitally generate… |
| img2table (`img2table`) | MIT | Free (OSS) | varies | — | ~ | ✗ | ✓ | Extracting structured tables (including merged cells and bo… |
| owocr (`owocr`) | GPL-3.0-only | Free (OSS) | varies | — | ~ | ✗ | ✗ | Real-time, on-screen Japanese text capture for language lea… |

### 4b. Remote / cloud services

| Service | Pricing | Accuracy | Langs | Hand | Math | Tables | Best for |
|---|---|---|---|---|---|---|---|
| ABBYY Cloud OCR SDK / Document AI… (`abbyy-cloud-ocr`) | Free tier+paid | excellent | 200 | ~ | ✗ | ✓ | High-accuracy enterprise document conversion at scale (im… |
| Azure AI Document Intelligence (f… (`azure-document-intelligence`) | Free tier+paid | excellent | 189 | ✓ | ✓ | ✓ | Production intelligent document processing on Azure where… |
| Extend (`extend`) | Free tier+paid | excellent | — | ✓ | ✓ | ✓ | Production document-processing pipelines for regulated/co… |
| Google Cloud Vision API (TEXT_DET… (`google-vision`) | Free tier+paid | excellent | 70 | ✓ | ✗ | ~ | General-purpose cloud OCR at scale: extracting printed te… |
| Google Gemini Vision (1.5 / 2.x /… (`gemini-vision`) | Free tier+paid | excellent | 37 | ✓ | ✓ | ✓ | Teams that want one API to do OCR plus understanding — ex… |
| Mathpix (Snip + Convert API) (`mathpix`) | Freemium | excellent | 33 | ✓ | ✓ | ✓ | Digitizing STEM content — math/physics equations, chemist… |
| Mistral OCR API (Document AI) (`mistral-ocr`) | Pay-as-you-go | excellent | — | ✓ | ✓ | ✓ | High-volume, low-cost conversion of PDFs and scanned/phot… |
| Reducto (`reducto`) | Free tier+paid | excellent | 100 | ✓ | ? | ✓ | Enterprise teams (finance, insurance, healthcare) parsing… |
| Veryfi OCR API (`veryfi`) | Free tier+paid | excellent | 39 | ✓ | ✗ | ✓ | High-volume, structured extraction of receipts and invoic… |
| AWS Rekognition DetectText (`aws-rekognition-detecttext`) | Free tier+paid | good | 8 | ✗ | ✗ | ✗ | Reading short bursts of text from real-world photos and s… |
| AWS Textract (`aws-textract`) | Pay-as-you-go | good | 6 | ~ | ✗ | ✓ | Teams already on AWS that need scalable, managed extracti… |
| Adobe PDF Extract API (PDF Servic… (`adobe-pdf-extract`) | Free tier+paid | good | — | ✗ | ✗ | ✓ | Extracting clean structured content (text blocks, heading… |
| Anthropic Claude Vision (Opus / S… (`claude-vision`) | Pay-as-you-go | good | — | ✓ | ✓ | ✓ | Prompt-driven extraction from complex, mixed documents (f… |
| Azure AI Document Intelligence (R… (`azure-document-intelligence-read`) | Free tier+paid | good | 300 | ✓ | ✓ | ✗ | Cloud-based, high-volume extraction of printed AND handwr… |
| Google Cloud Document AI (`google-document-ai`) | Pay-as-you-go | good | 200 | ✓ | ✓ | ✓ | Enterprises on Google Cloud needing managed, scalable OCR… |
| Google Cloud Vision (DOCUMENT_TEX… (`google-cloud-vision-handwriting`) | Free tier+paid | good | — | ✓ | ✗ | ✗ | Production document and handwriting OCR at scale where a … |
| Klippa DocHorizon OCR API (`klippa`) | Quote | good | 150+ | ~ | ✗ | ✓ | Structured data extraction from business documents — rece… |
| LlamaParse (`llamaparse`) | Free tier+paid | good | — | ✓ | ✓ | ✓ | Teams building RAG/agent pipelines on complex, visually r… |
| Mindee (`mindee`) | Free tier+paid | good | — | ~ | ✗ | ✓ | Teams that want fast, training-free structured-JSON extra… |
| OCR.space OCR API (`ocr-space`) | Freemium | good | 200 | ~ | ✗ | ✓ | Quick, low-cost extraction of plain text from clean print… |
| OpenAI GPT-4o / GPT-4.1 Vision (`gpt-4o-vision`) | Pay-as-you-go | good | — | ✓ | ✓ | ✓ | Flexible document understanding where you need extraction… |
| Taggun Receipt OCR (`taggun`) | Free tier+paid | good | 205 | ~ | ✗ | ~ | Production receipt and invoice data extraction at scale —… |
| Upstage Document Parse / Document… (`upstage-document-parse`) | Pay-as-you-go | good | — | ~ | ✓ | ✓ | RAG ingestion and LLM-ready conversion of complex, layout… |
| Pen2Txt (`pen2txt`) | Free tier+paid | varies | — | ✓ | ? | ✗ | Individuals and small teams (students, researchers, profe… |

### 4c. Cloud pricing (per the ledger `price_note`, as-of 2026-06)

| Service | Pricing model | Price | Free tier |
|---|---|---|---|
| ABBYY Cloud OCR SDK / Document … | Free tier+paid | No public list pricing (as of 2026-06). Legacy Cloud OCR … | Legacy Cloud OCR SDK: 500 A4 pages (or 25… |
| AWS Rekognition DetectText | Free tier+paid | As of 2026-06 (US East, Group 2 APIs tier that includes D… | AWS Free Tier: 1,000 images/month free fo… |
| AWS Textract | Pay-as-you-go | As of 2026-06 (US East/US West Oregon, on-demand, per 1,0… | Free Tier lasts 3 months from first use (… |
| Adobe PDF Extract API (PDF Serv… | Free tier+paid | As of 2026-06: Free tier = 500 Document Transactions/mont… | 500 Document Transactions per month, free… |
| Anthropic Claude Vision (Opus /… | Pay-as-you-go | As of June 2026, billed per token (not per page). Claude … | New Anthropic Console developer accounts … |
| Azure AI Document Intelligence … | Free tier+paid | As of 2026-06: Read OCR (S0 paid tier) is $1.50 per 1,000… | F0 tier: 500 pages/month free, but proces… |
| Azure AI Document Intelligence … | Free tier+paid | Pay-as-you-go (US, S0 tier, as of 2026-06): Read OCR ~$1.… | Free tier (F0): 500 free pages per month,… |
| Azure AI Vision Read OCR (Compu… | Free tier+paid | As of 2026-06: Free tier (F0) = 5,000 transactions/month,… | F0 free tier: 5,000 transactions/month, m… |
| Extend | Free tier+paid | As of 2026-06: credit-based, "you pay per page" via credi… | 10,000 free credits on the Pay-As-You-Go … |
| Google Cloud Document AI | Pay-as-you-go | As of 2026-06: Enterprise Document OCR $1.50/1,000 pages … | No standing per-month free page allowance… |
| Google Cloud Vision (DOCUMENT_T… | Free tier+paid | As of 2026-06: DOCUMENT_TEXT_DETECTION is billed at $1.50… | First 1,000 units/month free (per feature… |
| Google Cloud Vision API (TEXT_D… | Free tier+paid | As of 2026-06: TEXT_DETECTION and DOCUMENT_TEXT_DETECTION… | 1,000 units/month free (plus the standard… |
| Google Gemini Vision (1.5 / 2.x… | Free tier+paid | As of 2026-06, token-billed per the Gemini API pricing pa… | Yes. Google AI Studio / Gemini API free t… |
| Klippa DocHorizon OCR API | Quote | No public per-page price list (as of 2026-06). Klippa's o… | Free trial with €25.00 of free credit on … |
| Llama 3.2 Vision (11B / 90B) | Mixed | Weights are free to download and self-host (compute is yo… | Self-hosting is free of license fees (you… |
| LlamaParse | Free tier+paid | As of 2026-06: credit-based, 1,000 credits = $1.25 (same … | 10,000 free credits per month on the Free… |
| Marker (Datalab) | Mixed | As of 2026-06: Self-hosted is free (GPLv3 code; weights f… | Self-hosting is fully free under license … |
| Mathpix (Snip + Convert API) | Freemium | As of 2026-06. Convert API (pay-as-you-go): images $0.002… | Convert API: $29 free testing credit for … |
| Mindee | Free tier+paid | As of 2026-06: Free plan = 250 pages/month, no credit car… | 250 pages/month free, no credit card requ… |
| MinerU | Freemium | Self-hosted OSS is free. Hosted mineru.net API is in free… | Self-hosted: fully free/unlimited (own co… |
| MiniCPM-V (4.5 / 4.6) | Free (OSS) | Free open-weight model (Apache-2.0) for self-hosting; no … | Fully free for local/self-hosted use (wei… |
| Mistral OCR API (Document AI) | Pay-as-you-go | As of 2026-06: OCR text extraction $2 per 1,000 pages (~5… | No dedicated free OCR tier. New la Platef… |
| Nanonets | Freemium | As of 2026-06: Sign-up gives $200 prepaid credits (no car… | $200 in prepaid credits on signup (never … |
| OCR.space OCR API | Freemium | As of 2026-06: Free tier $0. PRO $30/month (300,000 reque… | Free API key ("helloworld" demo key plus … |
| OpenAI GPT-4o / GPT-4.1 Vision | Pay-as-you-go | As of 2026-06 (standard API tier): GPT-4o = $2.50/1M inpu… | No standing free OCR/vision tier. New acc… |
| PaddleOCR (PP-OCRv5 / PaddleOCR… | Free (OSS) | The toolkit and all models (PP-OCRv5/v6, PaddleOCR-VL, PP… | Fully free and unlimited when self-hosted… |
| PaddleOCR 3.0 / PP-StructureV3 | Free (OSS) | Software is free (Apache-2.0) to self-host; you pay only … | Fully free to self-host (unlimited, your … |
| Pen2Txt | Free tier+paid | As of 2026-06 (EUR, monthly subscription, credit-based; ~… | Yes — free trial granting 3 credits (~3 p… |
| Qwen2-VL / Qwen2.5-VL / Qwen3-VL | Mixed | Open weights are free to self-host. Via Alibaba Cloud Mod… | Self-hosting is free (Apache-2.0 weights,… |
| Reducto | Free tier+paid | As of 2026-06: credit-based. Standard plan is pay-as-you-… | 15,000 free credits on signup (≈ 7,500-15… |
| Surya OCR | Freemium | As of 2026-06: OSS self-host is free under the weights li… | Fully free for self-hosting under the wei… |
| Taggun Receipt OCR | Free tier+paid | As of 2026-06 (USD): Developer $28/mo (500 scans, ~$0.056… | 30-day free trial with unlimited scans (n… |
| Texify / Surya (LaTeX OCR) | Free tier+paid | Self-hosted OSS is free (subject to model license). Datal… | Unlimited local/self-hosted use (Apache-2… |
| Unstructured.io API | Free tier+paid | As of 2026-06: hosted Serverless API is pay-as-you-go at … | 15,000 free pages, no expiration, full fe… |
| Upstage Document Parse / Docume… | Pay-as-you-go | As of 2026-06: Document Parse Standard $0.01/page, Enhanc… | Free sign-up credits for new users plus 1… |
| Veryfi OCR API | Free tier+paid | As of 2026-06 (USD): Free plan = 100 documents/month, $0.… | 100 documents/month free forever (not a t… |
| dots.ocr | Free (OSS) | The model itself is free (MIT, open weights) — self-host … | Fully free to self-host (open weights, MI… |
| owocr | Free (OSS) | The owocr software is free and open-source (GPL-3.0); no … | Entirely free as software with unlimited … |


## 5. Recommended roadmap

Wave 1 (the 10-backend shortlist, each mapped to feature scope), Wave 2 (surya, trocr-handwritten, aws-textract, olmocr/mineru, docling, table-transformer/img2table/camelot), and the ~40 ledger-only rows grouped by reason (legacy/dormant, redundant, heavy VLM zoo, niche IDP, DH/historical).

## References

Primary sources for the engines discussed above and every implemented backend. **Exhaustive per-engine citations** (2–6 each, adversarially fact-checked) live in the `citations` field of every record in `ocracy/data/backends.json`.

1. [github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)
2. [github.com/JaidedAI/EasyOCR](https://github.com/JaidedAI/EasyOCR)
3. [github.com/RapidAI/RapidOCR](https://github.com/RapidAI/RapidOCR)
4. [github.com/PaddlePaddle/PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR)
5. [github.com/straussmaximilian/ocrmac](https://github.com/straussmaximilian/ocrmac)
6. [mindee.github.io/doctr](https://mindee.github.io/doctr/)
7. [github.com/mindee/doctr](https://github.com/mindee/doctr)
8. [github.com/datalab-to/surya](https://github.com/datalab-to/surya)
9. [docling-project.github.io/docling](https://docling-project.github.io/docling/)
10. [github.com/docling-project/docling](https://github.com/docling-project/docling)
11. [github.com/datalab-to/marker](https://github.com/datalab-to/marker)
12. [github.com/opendatalab/MinerU](https://github.com/opendatalab/MinerU)
13. [olmocr.allenai.org](https://olmocr.allenai.org/)
14. [github.com/allenai/olmocr](https://github.com/allenai/olmocr)
15. [github.com/Ucas-HaoranWei/GOT-OCR2.0](https://github.com/Ucas-HaoranWei/GOT-OCR2.0)
16. [github.com/rednote-hilab/dots.ocr](https://github.com/rednote-hilab/dots.ocr)
17. [github.com/deepseek-ai/DeepSeek-OCR](https://github.com/deepseek-ai/DeepSeek-OCR)
18. [facebookresearch.github.io/nougat](https://facebookresearch.github.io/nougat/)
19. [github.com/facebookresearch/nougat](https://github.com/facebookresearch/nougat)
20. [huggingface.co/docs/transformers/model_doc/trocr](https://huggingface.co/docs/transformers/model_doc/trocr)
21. [huggingface.co/microsoft/trocr-large-handwritten](https://huggingface.co/microsoft/trocr-large-handwritten)
22. [kraken.re](https://kraken.re/)
23. [github.com/Calamari-OCR/calamari](https://github.com/Calamari-OCR/calamari)
24. [ocr4all.org](https://www.ocr4all.org/)
25. [github.com/OCR4all/OCR4all](https://github.com/OCR4all/OCR4all)
26. [github.com/AuroraWright/owocr](https://github.com/AuroraWright/owocr)
27. [github.com/xavctn/img2table](https://github.com/xavctn/img2table)
28. [github.com/microsoft/table-transformer](https://github.com/microsoft/table-transformer)
29. [camelot-py.readthedocs.io](https://camelot-py.readthedocs.io/)
30. [github.com/camelot-dev/camelot](https://github.com/camelot-dev/camelot)
31. [cloud.google.com/vision/docs/ocr](https://cloud.google.com/vision/docs/ocr)
32. [cloud.google.com/document-ai/docs](https://cloud.google.com/document-ai/docs)
33. [cloud.google.com/document-ai/docs/processors-list](https://cloud.google.com/document-ai/docs/processors-list)
34. [aws.amazon.com/textract](https://aws.amazon.com/textract/)
35. [aws.amazon.com/textract/pricing](https://aws.amazon.com/textract/pricing/)
36. [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)
37. [ocrsdk.com](https://www.ocrsdk.com/)
38. [ocr.space/ocrapi](https://ocr.space/ocrapi)
39. [mathpix.com](https://mathpix.com/)
40. [mathpix.com/pricing/api](https://mathpix.com/pricing/api)
41. [github.com/lukas-blecher/LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR)
42. [mistral.ai/news/mistral-ocr](https://mistral.ai/news/mistral-ocr)
43. [platform.openai.com/docs/guides/images](https://platform.openai.com/docs/guides/images)
44. [developers.openai.com/api/docs/guides/images](https://developers.openai.com/api/docs/guides/images)
45. [ai.google.dev/gemini-api/docs/vision](https://ai.google.dev/gemini-api/docs/vision)
46. [platform.claude.com/docs/en/docs/build-with-claude/vision](https://platform.claude.com/docs/en/docs/build-with-claude/vision)
47. [nanonets.com/ocr-api](https://nanonets.com/ocr-api)
48. [veryfi.com/receipt-ocr-api](https://www.veryfi.com/receipt-ocr-api/)
