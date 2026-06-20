# The OCR Landscape: Engines, Services, and Build-vs-Wrap Analysis for the `ocracy` Facade Package

*As-of date: 2026-06. Decision-grade reference for the `ocracy` facade architecture.*

---

## 1. Executive summary

1. **Build a fresh, thin facade — do not wrap an existing aggregator.** The candidate "facades" each carry a worldview that conflicts with `ocracy`'s goal of *one uniform call over heterogeneous backends*. `pyocr` is unmaintained and narrow; **RapidOCR** [6] is a single-engine deployment shell (ONNX PaddleOCR), not a multi-backend facade; **Surya** [9], **docling** [20], and **unstructured** [35] are document-ETL/parsing pipelines whose object model (typed document elements, chunking, Markdown ETL) is heavier and more opinionated than a `text + boxes + confidence` result type. The closest precedents — `owocr` [17] and `img2table` [44] — *are* multi-backend dispatchers, and they validate the pattern (`owocr` already unifies ~15 local + cloud engines behind one CLI), but both are domain-scoped (Japanese on-screen text; tables). The right move is the `denote`/`aix` sibling pattern already scaffolded: a normalized `OcrResult`, a data-driven ledger, lazy per-backend extras, and a scaffold workflow. Wrap *engines*, not *another facade*.

2. **A normalized result type is feasible across the whole field, but two capabilities resist normalization.** Almost every backend yields text + word/line bounding boxes + per-element confidence (Tesseract [1], EasyOCR [2], docTR [4], cloud APIs [22][24][26]). Two axes break the lowest common denominator: (a) **bounding boxes/confidence vanish in VLM/LLM OCR** (GPT-4o [37], Claude [38], Nougat [21], GOT-OCR2.0 [10] expose neither natively); (b) **"beyond-text" output** (Markdown, LaTeX math, HTML tables) is structured, not a flat string. `ocracy`'s `result.markdown` / `result.raw` escape hatches already account for this; treat boxes/confidence as `Optional`.

3. **The local/open-source tier is strong enough that most users never need a paid API.** For commodity printed text, **PaddleOCR (PP-OCRv5/v6)** [3] and **RapidOCR** [6] give near-SOTA accuracy on CPU, Apache-2.0, 100+ languages, with tables/math/handwriting in the VL variant. **Tesseract** [1] remains the zero-friction baseline. The paid tier earns its keep only for (a) managed scale without GPU ops, (b) turnkey structured extraction (invoices/IDs), or (c) frontier handwriting/multilingual where you lack a GPU.

4. **VLM OCR has overtaken specialized engines on document-parsing benchmarks but is the wrong default.** On OmniDocBench v1.5/v1.6, PaddleOCR-VL (~96%) [3], dots.ocr [18], DeepSeek-OCR [19], and MinerU [20] lead, beating GPT-4o and Gemini on text/tables/reading-order. But VLMs hallucinate, lack boxes/confidence, need a GPU, and bill per token. Keep them as *opt-in power backends*, not the facade default.

5. **Pricing clusters into three bands.** Commodity cloud OCR ≈ **$1.50/1,000 pages** (Google Vision [22], Azure DI Read [42], AWS Textract raw [24], Azure DI [27]); VLM-OCR APIs are cheaper still — **Mistral OCR $2/1k (→$1 batch)** [36], self-hosted olmOCR **~$0.0002/page** [16]; structured IDP is far pricier — **AWS Forms $50/1k, Textract Forms+Tables+Queries $70/1k** [24], Google Form Parser **$30/1k** [23]. Self-hosted OSS is free + your compute.

6. **Recommended first-implementation shortlist (10 backends).** Spans local/remote, free/paid, and beyond-text:
   - **Local + free:** `tesseract` [1] (baseline), `paddleocr` [3] (accuracy + math/tables/handwriting), `easyocr` [2] (pip-only multilingual), `rapidocr` [6] (fast ONNX, no Paddle dep), `ocrmac` [14] (Apple Vision, zero-dep on macOS).
   - **Remote + paid/freemium:** `google-vision` [22] (gold-standard cloud baseline, handwriting), `azure-document-intelligence` [27] or `aws-textract` [24] (tables + key-value), `mistral-ocr` [36] (cheap VLM Markdown/math/tables).
   - **Beyond-text specialists:** `mathpix` [49] (math/LaTeX + handwriting, remote) **and/or** `pix2tex` [50] (math, local free); `trocr-handwritten` [47] (local handwriting); `surya` [9] (local VLM: tables + inline math + 91 languages).
   - This set guarantees: ≥4 local, ≥3 remote, ≥4 free, ≥3 paid, and covers math (`mathpix`/`pix2tex`/`surya`), tables (`paddleocr`/`azure`/`surya`), and handwriting (`trocr-handwritten`/`google-vision`/`mathpix`).

7. **Leave the long tail in the ledger, unimplemented but discoverable.** ~50 of the 64 researched options should ship as catalog rows only — legacy engines (OCRopus [13], MMOCR [8], keras-ocr [12]), niche specialists (Veryfi [55], Taggun [56], Klippa [29], Pen2Txt [54]), and the heavy VLM zoo (Qwen-VL [40], InternVL [41], dots.ocr [18], DeepSeek-OCR [19], MinerU [20]). The `implemented` flag computed live from code (per the README) keeps the ledger honest about what runs today.

8. **The ledger schema is the product's moat.** The differentiator vs. any single engine is the *decision layer*: `find(is_local=True, open_source=True)`, `can("math")`, `supports_language("Arabic")`, `compare([...])`. The feature axes in §2 below justify each schema field; keep them populated and dated, because pricing, model versions, and leaderboards churn fast (e.g., GPT-4o/4.1 retired from ChatGPT Feb 2026 [37]; Gemini 1.5/2.0 shut down [39]; ABBYY Cloud OCR SDK end-of-sale [28]).

---

## 2. What features matter for choosing an OCR backend

These axes are the columns of the ledger; each exists because it changes a real build-or-buy decision.

- **Local vs. remote (`is_local` / `is_remote`).** The single most consequential axis. Local engines (Tesseract, PaddleOCR, EasyOCR, docTR) keep data on-machine — mandatory for air-gapped, regulated, or privacy-sensitive work — and cost only compute. Remote APIs (Google, Azure, AWS, Mistral, OpenAI) trade data egress for zero-ops scale and frontier models. Several backends are *both*: PaddleOCR [3], MinerU [20], Surya [9], Qwen-VL [40], dots.ocr [18], Nanonets [33], Mistral [36] (self-host license), and PaddleOCR-VL all offer self-host + hosted.

- **Pricing model (`pricing_model`, `price_note`, `free_tier`).** Five regimes: `free_oss` (Tesseract, PaddleOCR, docTR), `freemium` (Surya, OCR.space, MinerU, Nanonets), `free_tier_then_paid` (Google Vision, Azure, OCR.space, Mindee, LlamaParse), `pay_as_you_go` (Document AI, Textract, Mistral, GPT-4o, Gemini), and `proprietary_quote` (Klippa, ABBYY). Normalizing to **per-1,000-pages** (§4.ii) is essential because token-billed VLMs and credit-based IDP obscure true cost.

- **Accuracy (`accuracy_tier`, `accuracy_note`).** No universal metric. Three reference frames recur: **CER/WER** on line recognition (TrOCR 2.89% CER on IAM [7]; Calamari ~0.1–0.2% on clean print [11]); **OmniDocBench / OCRBench** edit-distance for full-page parsing (PaddleOCR-VL ~96% [3], dots.ocr 0.032 EN edit distance [18]); and **table TEDS** / **olmOCR-bench** for structure (Reducto ~90% RD-TableBench [31], olmOCR 82.4 [16]). Always note whether a figure is vendor-reported or independent — most VLM headline numbers are vendor-run.

- **Language / script coverage (`languages_count`, `languages_note`).** Ranges from English-only (keras-ocr [12], olmOCR [16], Nougat [21]) to 200+ (Google Document AI [23], OCR.space Engine 3 [30], Taggun [56]). Script families (Latin, CJK, Cyrillic, Arabic, Indic, Hebrew, Thai) matter more than raw counts; handwriting coverage is almost always a narrower subset (Azure: 300+ printed but 12 handwritten [27][42]; AWS Textract: English-only handwriting [24]).

- **Handwriting (`handwriting`).** A discriminator, not a given. Strong: TrOCR [7][47], Mathpix [49], Kraken [11], Google Vision [22][52], Surya [9], the VLM tier. Absent: Tesseract [1], keras-ocr [12], winocr [15], AWS Rekognition [25], Adobe Extract [32], Nougat [21].

- **Math / formulas (`math_formula`).** Specialized capability. Best-in-class: Mathpix [49], pix2tex [50], Nougat [21], GOT-OCR2.0 [10]; also in PaddleOCR-VL [3], Surya [9], olmOCR [16], Mistral [36], the VLMs. Most classical engines and cloud OCR (Google Vision, Textract, Azure Read) cannot read formulas.

- **Tables (`tables`).** Three approaches: native engine support (PaddleOCR PP-StructureV3 [48], Surya [9], cloud IDP), dedicated extractors (Table Transformer [43], img2table [44], Camelot [45], Tabula [46]), and VLM Markdown/HTML output. Table TEDS scores cluster 80–96% with Reducto [31], Mistral [36], and dots.ocr [18] at the top.

- **Layout / structure / reading order (`layout_structure`).** Distinguishes plain OCR (word boxes only — Tesseract, EasyOCR) from document parsers (docTR [4], MinerU [20], Docling [20], PaddleOCR-VL [3]) that recover reading order, headers, multi-column flow, and emit Markdown/JSON.

- **Output formats (`markdown`, `raw`).** Plain text + boxes vs. searchable PDF/hOCR/ALTO (Tesseract, Kraken, ABBYY) vs. Markdown/LaTeX/HTML for LLM ingestion (the VLM and document-parser tier). `ocracy`'s `result.markdown` surfaces the latter without forcing it.

- **Bounding boxes & confidence (`bounding_boxes`, `confidence_scores`).** Load-bearing for redaction, search-highlight, and human-in-the-loop gating. Present in classical OCR and cloud APIs; **absent in most generative VLMs** — a key reason to keep them `Optional` in the normalized type.

- **Privacy (`privacy_note`).** Derived from local/remote but worth its own field: air-gap capability, data-retention terms, EU regions, on-prem containers (Azure [27], ABBYY [28]), and zero-data-retention options (Reducto [31], Claude [38]).

- **GPU (`gpu_recommended`).** Determines deployment cost. Classical engines run CPU-only (Tesseract, RapidOCR, Calamari); neural recognizers benefit from GPU (EasyOCR, docTR); VLMs effectively *require* one (olmOCR, DeepSeek-OCR, Qwen-VL, dots.ocr).

- **Maturity (`maturity_note`).** Guards against shipping a facade over a dead engine. Live signals: last release date, GitHub stars, archive status. The field already catches OCRopus (archived 2026-04 [13]), MMOCR (last release 2023 [8]), keras-ocr (quasi-dormant [12]), Nougat (dormant [21]), and ABBYY Cloud OCR SDK (end-of-sale [28]).

---

## 3. Category deep-dives

### (a) Local / open-source general engines

**Tesseract** [1] is the durable baseline: Apache-2.0, CPU-only, 100+ languages, rich structured output (hOCR/ALTO/TSV, word boxes, confidence), and packaged everywhere. On clean print it reaches ~98–99% character accuracy, but it collapses on noise/skew (receipt-study CER ~15.6%) and has no handwriting, math, or table-structure support. It is consistently beaten on OmniDocBench by **PaddleOCR** [3] — the standout of this tier. PaddleOCR offers two complementary engines: an ultra-light PP-OCRv5/v6 pipeline (~4 MB mobile models, CPU/edge) and PaddleOCR-VL (0.9B VLM) reporting ~96% on OmniDocBench v1.6, beating GPT-4o/Gemini on doc parsing, with math/tables/charts/handwriting and 109 languages. Its cost is a heavy, version-sensitive PaddlePaddle install. **EasyOCR** [2] (Apache-2.0, ~86 languages, pip-only, no Paddle dependency) is the friction-free multilingual choice — strong on scene text, weaker on dense documents, slowing maintenance (last release Sep 2024). **RapidOCR** [6] ports PaddleOCR's models to ONNX, giving Paddle-level accuracy without the framework, plus genuine cross-platform/polyglot bindings — ideal when you want PaddleOCR quality but a lightweight install. **docTR** [4] / **OnnxTR** [5] (Apache-2.0, Mindee/t2k) offer a clean modular detect+recognize architecture with swappable backbones, competitive with Google Vision/Textract on FUNSD/CORD, but Latin-centric out of the box. **ocrmac** [14] wraps Apple Vision: free, fully on-device, ~130–210 ms/image on Apple Silicon, ~18 languages — an excellent zero-dependency default for Mac users (but macOS-only). **winocr** [15] is its Windows analogue (free, on-device, 25 languages, no confidence scores).

For **historical/non-Latin and HTR**, the digital-humanities stack stands apart: **Kraken** [11] (Apache-2.0, trainable, native RTL/BiDi/vertical scripts, historical models via Zenodo) and **Calamari** [11] (GPL-3.0, ~0.1–0.2% CER on clean print via 5-fold voting) are state-of-the-art on archival material *when you train a model*, integrated via **OCR4all** [21] and the eScriptorium UI. **OCRopus** [13] is their archived ancestor (read-only since 2026-04) — keep it as a ledger row, not a backend. **MMOCR** [8] (research toolbox, last release 2023) and **keras-ocr** [12] (English-only, quasi-dormant) are similarly best left unimplemented.

### (b) Cloud OCR & document-AI APIs

The "big three" anchor the commodity tier at **~$1.50/1,000 pages**. **Google Cloud Vision** [22] (`DOCUMENT_TEXT_DETECTION`) is the gold-standard general cloud OCR: 70+ supported languages (200+ claimed), genuine handwriting, full page/block/word hierarchy with boxes and confidence, top content-similarity in the Nanonets benchmark (~75% FUNSD, ~88% SROIE). **AWS Textract** [24] and **Azure AI Vision / Document Intelligence** [26][27][42] match it on printed text (~95–99%) and pull ahead on *structured* extraction — tables, key-value forms, IDs, invoices — but at IDP prices (Textract Forms $50/1k, Forms+Tables+Queries $70/1k; Azure DI Layout/prebuilt $10/1k, custom $30/1k). Textract's catch is language: only 6 Latin-script languages for print, English-only handwriting. Azure DI is the broadest of the three (300+ printed languages, 12 handwritten, math/barcode add-ons, on-prem containers) and tops AImultiple's 2025 printed-text benchmark (~96%). **Google Document AI** [23] is the structured-extraction counterpart to Vision: 200+ languages, pretrained invoice/receipt/ID parsers, math-to-LaTeX, checkbox/quality add-ons — but its table parser drops to ~40% on complex layouts. **AWS Rekognition DetectText** [25] is scene-text only (100-word cap, no handwriting/tables) — not a document OCR. **ABBYY** [28] remains the mature commercial reference engine (200+ languages, rich export, OMR/barcodes) but its Cloud OCR SDK is end-of-sale; new users get routed to the technical-preview Document AI API with no public pricing.

A second cloud tier targets **RAG/LLM ingestion and IDP**: **OCR.space** [30] (generous free tier, 200+ languages Engine 3, ~$30–60/mo) is the cheap prototyping choice; **Mindee** [26], **Nanonets** [33], **Klippa** [29], **Reducto** [31], **Extend** [34], **Upstage** [30], **Adobe PDF Extract** [32], **LlamaParse** [30], and **Unstructured** [35] all convert documents to structured JSON/Markdown. Standouts: **Reducto** ~90% on its own RD-TableBench (ahead of Azure/AWS/Google/GPT-4o) [31]; **Nanonets** dual-offers a no-code IDP platform *and* free open-weight VLM models [33]; **Unstructured** is uniquely Apache-2.0 at its core with a free self-host fallback [35]. For receipts/invoices specifically, **Veryfi** [55] and **Taggun** [56] are domain specialists (Veryfi claims ~99.5% line-item accuracy). All are cloud-first with vendor-reported benchmarks — treat accuracy claims skeptically and gate on confidence scores where available.

### (c) LLM / VLM-based OCR

This category has reshaped the leaderboards. **Self-hostable open-weight VLMs** dominate OmniDocBench: **PaddleOCR-VL** [3] (~96% v1.6), **dots.ocr** [18] (0.032 EN edit distance, beating Gemini 2.5 Pro/GPT-4o, MIT, ~3B), **DeepSeek-OCR** [19] (MIT, ~100 languages, novel token-compression, ~200k pages/day on one A100), and **MinerU** [20] (top-tier, free hosted beta of 2,000 pages/day). **olmOCR** [16] (Ai2, Apache-2.0 code *and* weights) is the cost-efficiency champion at **~$190/million pages** self-hosted, near-SOTA on its own olmOCR-bench (82.4), but English-only. **GOT-OCR2.0** [10] pioneered the unified ~580M model (text+math+tables+charts+music) but has been overtaken. General-purpose VLMs — **Qwen2.5/3-VL** [40] (Apache-2.0, OCRBench 874, 32 languages), **InternVL3.5** [41] (OCRBench 907), **MiniCPM-V** [40] (runs on a phone), **Llama 3.2 Vision** [40] (English-only OCR, trailing) — add OCR-plus-reasoning but at GPU cost.

**Hosted frontier VLMs** — **GPT-4o/4.1** [37] (OmniDocBench ~86.6), **Claude** [38] (Sonnet ~7th on socOCRbench), **Gemini** [39] (Gemini 3 Pro ~0.115 OmniDocBench, OCRBench ~87.6) — excel at *understanding* (extraction + reasoning + JSON-schema output in one call, strong handwriting/charts) but: no native boxes/confidence, token-billed and unpredictable, prone to hallucination/omission on dense pages, and weaker on non-Latin scripts. **Mistral OCR** [36] is the pragmatic VLM-OCR API: commodity-priced ($2/1k, $1 batch), strong vendor benchmark (94.89%), Markdown/tables/math/handwriting, self-host license available. Across this tier the universal caveat: **VLMs can silently invent or drop text**, so they belong as opt-in power backends with downstream validation, never as a coordinate-dependent or compliance-critical default.

### (d) Specialized (math, tables, handwriting, receipts, music/OMR, barcodes)

**Math:** **Mathpix** [49] is best-in-class for STEM — printed *and* handwritten equations, chemistry to SMILES, tables to LaTeX/Markdown, with boxes and confidence, cheap pay-as-you-go (~$0.002/image), and an on-prem container; **pix2tex/LaTeX-OCR** [50] is the free local MIT baseline (single-equation, BLEU ~0.88) and **Texify/Surya** [51] its actively-maintained successor; **Nougat** [21] converts academic PDFs to Mathpix-Markdown but is dormant and weights are non-commercial.

**Tables:** beyond the cloud IDP and VLMs, three free local tools matter: **Table Transformer (TATR)** [43] (MIT, excellent cell-structure GriTS, but detects geometry only — needs separate OCR for text), **img2table** [44] (MIT, OpenCV detection + *pluggable* OCR backend — interesting as a composition target since it already wraps Tesseract/Paddle/EasyOCR/docTR/Surya/RapidOCR), **Camelot** [45] and **Tabula** [46] (MIT, native-PDF text-layer extraction — not image OCR; strong on ruled tables, collapse on borderless).

**Handwriting:** **TrOCR-handwritten** [47] (MIT, ~2.89% CER on IAM, English single-line — needs external segmentation) is the local champion; **Google Vision** [52] and **Azure DI Read** [42] are the cloud options; **Pen2Txt** [54] is a niche indie SaaS for note digitization (no API). **Receipts:** **Veryfi** [55], **Taggun** [56], plus Textract/Document AI Expense parsers. **Music/OMR & barcodes** are thin: GOT-OCR2.0 [10] and Qwen-VL [40] read sheet music; barcodes appear as side-features in cloud IDP (Google Vision [22], ABBYY [28], Nanonets [33], Extend [34]) — no dedicated OSS OMR/barcode engine is in scope, so these remain capability flags rather than backends.

### (e) Existing Python facades / aggregators (the build-vs-wrap evidence)

This is the crux. The honest multi-backend dispatchers among the 64 are **`owocr`** [17] and **`img2table`** [44], and they *prove the facade pattern works* — `owocr` already routes ~10 local + 5 cloud engines (Apple Vision, WinRT, EasyOCR, RapidOCR, Google Vision, Azure, OCR.space…) behind one interface; `img2table` pluggably swaps six OCR backends under a table extractor. But both are domain-scoped (on-screen Japanese; tables) and GPL-licensed, so neither is a base to wrap — they are *design precedents* confirming `ocracy`'s thesis. The other "facade-like" projects are actually **single-engine deployment shells or document-ETL pipelines**: **RapidOCR** [6] (one engine, ONNX), **Surya** [9] / **Marker** [20] (Datalab's own VLM pipeline), **MinerU** [20], **Docling** [20] (IBM's parser that *itself* wraps Tesseract/EasyOCR/RapidOCR/Apple Vision — the nearest thing to a facade, but with a heavy typed-element ETL object model and RAG-chunking focus), **Unstructured** [35] (document ETL), and **LlamaParse** [30] (cloud RAG parser). Wrapping any of these would inherit its worldview — typed document elements, Markdown chunking, a single fixed engine — and fight `ocracy`'s flat `OcrResult`. **Conclusion: build fresh.** The verified evidence is that no existing package offers an engine-agnostic `text + boxes + confidence` facade with a comparison ledger across local *and* remote *and* VLM backends — which is precisely the gap `ocracy` fills.

---

## 4. Comparison tables

### (i-a) Master table — local / open-source engines

| Name | Local/Remote | License | Pricing | Accuracy | Languages | Handwriting | Math | Tables | Best for |
|---|---|---|---|---|---|---|---|---|---|
| Tesseract [1] | Local | Apache-2.0 | Free OSS | Good (~98% clean) | 116 | No | No | Limited | Zero-cost offline baseline |
| EasyOCR [2] | Local | Apache-2.0 | Free OSS | Good | 86 | Limited | No | No | Easy multilingual scene/print |
| PaddleOCR (v5/v6 + VL) [3] | Both | Apache-2.0 | Free OSS | Excellent (~96% OmniDoc) | 109 | Yes | Yes | Yes | Best free accuracy + structure |
| docTR [4] | Local | Apache-2.0 | Free OSS | Good | n/a (Latin) | Limited | No | Limited | Modular self-host pipeline |
| OnnxTR [5] | Local | Apache-2.0 | Free OSS | Good | ~100 vocab | No | No | No | Lightweight ONNX docTR |
| RapidOCR [6] | Local | Apache-2.0 | Free OSS | Good (PP-OCR) | 12 | Limited | No | Limited | Fast ONNX, no Paddle dep |
| TrOCR [7] | Local | MIT | Free OSS | Excellent (CER 2.89%) | n/a (EN) | Yes | No | No | English line recognition |
| Surya [9] | Both | Apache-2.0 / RAIL-M | Freemium | Good (olmOCR 83.3) | 91 | Limited | Yes | Yes | Self-host VLM: math+tables |
| GOT-OCR2.0 [10] | Local | Apache-2.0 | Free OSS | Good | n/a (EN/ZH) | Limited | Yes | Yes | Unified small model + music |
| Kraken [11] | Local | Apache-2.0 | Free OSS | Good (trained) | trainable | Yes | No | Limited | Historical / RTL / HTR |
| Calamari [11] | Local | GPL-3.0+ | Free OSS | Excellent (~0.1% CER) | trainable | Limited | No | No | Historical print transcription |
| ocrmac (Apple Vision) [14] | Local | MIT | Free OSS | Good | 18 | Limited | No | No | macOS on-device |
| winocr (Windows OCR) [15] | Local | MIT | Free OSS | Fair | 25 | No | No | No | Windows on-device |
| olmOCR [16] | Local | Apache-2.0 | Free OSS (~$0.0002/pg) | Excellent (82.4) | n/a (EN) | Yes | Yes | Yes | Bulk EN PDF→Markdown |
| dots.ocr [18] | Both | MIT | Free OSS | Excellent (0.032 ED) | 100 | Limited | Yes | Yes | Self-host SOTA doc parse |
| DeepSeek-OCR [19] | Local | MIT | Free OSS | Excellent (75.7) | 100 | Limited | Yes | Yes | High-throughput doc→text |
| MinerU [20] | Both | MinerU OSS Lic. | Freemium | Excellent (~95 VLM) | 109 | Limited | Yes | Yes | Complex PDF→Markdown |
| Docling [20] | Local | MIT | Free OSS | Good (pluggable) | 80 | Limited | Yes | Yes | Self-host doc ETL for RAG |
| Marker [20] | Both | GPL-3.0 / RAIL-M | Mixed | Excellent | 90 | Yes | Yes | Yes | Whole-doc→Markdown |
| Qwen-VL [40] | Both | Apache-2.0 | Mixed | Excellent (OCRBench 874) | 32 | Yes | Yes | Yes | Self-host multilingual VLM |
| InternVL [41] | Local | Apache/MIT | Free OSS | Excellent (OCRBench 907) | n/a | Limited | Yes | Yes | Self-host OCR+reasoning |
| pix2tex [50] | Local | MIT | Free OSS | Good (math) | n/a (math) | Limited | Yes | No | Free local equation→LaTeX |
| Table Transformer [43] | Local | MIT | Free OSS | Excellent (tables) | n/a | No | No | Yes | Table structure detection |
| img2table [44] | Local | MIT | Free OSS | Varies | n/a | Limited | No | Yes | Pluggable table extraction |
| trocr-handwritten [47] | Local | MIT (base) | Free OSS | Excellent (2.89% CER) | n/a (EN) | Yes | No | No | English handwriting lines |

### (i-b) Master table — cloud / remote services

| Name | Local/Remote | License | Pricing | Accuracy | Languages | Handwriting | Math | Tables | Best for |
|---|---|---|---|---|---|---|---|---|---|
| Google Cloud Vision [22] | Remote | Proprietary | $1.50/1k (1k free/mo) | Excellent | ~70 (200+ claimed) | Yes | No | Limited | General cloud OCR + handwriting |
| Google Document AI [23] | Remote | Proprietary | $1.50/1k OCR; $30/1k forms | Good | 200 | Yes | Yes | Yes | Structured IDP on GCP |
| AWS Textract [24] | Remote | Proprietary | $1.50/1k; $50/1k forms | Good | 6 | Limited (EN) | Yes | Yes | AWS IDP: tables/forms/IDs |
| AWS Rekognition DetectText [25] | Remote | Proprietary | ~$1.00/1k | Good | 8 | No | No | No | Scene/in-the-wild text |
| Azure AI Vision Read [26] | Both | Proprietary | ~$1.00–1.50/1k (5k free/mo) | Good | 164 | Yes | No | Limited | Real-time cloud OCR |
| Azure Document Intelligence [27] | Remote | Proprietary | $1.50/1k Read; $10/1k Layout | Excellent (~96%) | 189 | Yes | Yes | Yes | Enterprise IDP + on-prem |
| Azure DI Read OCR [42] | Remote | Proprietary | $1.50/1k (500 free/mo) | Good | 300 | Yes | Yes | No | Print+handwriting at scale |
| ABBYY Cloud OCR / Doc AI [28] | Remote | Proprietary | Quote (~$0.02–0.10/pg) | Excellent | 200 | Limited | No | Yes | Enterprise doc conversion |
| OCR.space [30] | Remote | Proprietary | Free / $30–60/mo | Good | 200 | Limited | No | Yes | Low-cost prototyping |
| Mindee [26] | Remote | Proprietary | 250 pg/mo free; ~$0.01–0.10/pg | Good | n/a | Limited | No | Yes | Prebuilt business-doc fields |
| Nanonets [33] | Both | Mixed | $200 credits; ~$2/doc | Excellent (vendor) | 12 | Yes | Yes | Yes | No-code IDP + open VLMs |
| Klippa DocHorizon [29] | Remote | Proprietary | Quote (€25 trial) | Good | 150+ | Limited | No | Yes | EU fintech IDP + fraud |
| Adobe PDF Extract [32] | Remote | Proprietary | 500/mo free; annual sub | Good | n/a (EN) | No | No | Yes | PDF tables→structured JSON |
| Upstage Document Parse [30] | Remote | Proprietary | $0.01–0.03/pg | Good | n/a (EN/CJK) | Limited | Yes | Yes | Korean/CJK RAG ingestion |
| Reducto [31] | Remote | Proprietary | 15k credits free; $0.015/pg | Excellent (~90% tables) | 100 | Yes | Unknown | Yes | Enterprise complex tables |
| Extend [34] | Remote | Proprietary | 10k credits free; $500/mo | Excellent (vendor) | n/a | Yes | Yes | Yes | Regulated-industry parsing |
| Unstructured.io [35] | Both | Apache-2.0 (core) | 15k pg free; $0.03/pg | Good | n/a | Limited | Yes | Yes | RAG ETL, free self-host |
| LlamaParse [30] | Remote | Proprietary | 10k credits/mo free | Good | n/a (100+) | Yes | Yes | Yes | LlamaIndex RAG pipelines |
| Mistral OCR [36] | Remote | Proprietary | $2/1k ($1 batch) | Excellent (94.89% vendor) | n/a (35+) | Yes | Yes | Yes | Cheap VLM Markdown/math |
| GPT-4o / 4.1 Vision [37] | Remote | Proprietary | Token-billed | Good (~86.6) | n/a (50+) | Yes | Yes | Yes | OCR+reasoning, JSON output |
| Claude Vision [38] | Remote | Proprietary | Token-billed | Good | n/a | Yes | Yes | Yes | Complex-doc extraction |
| Gemini Vision [39] | Both* | Proprietary | Free tier; token-billed | Excellent (~0.115) | 37 | Yes | Yes | Yes | OCR+understanding, long PDFs |
| Mathpix [49] | Remote | Proprietary | ~$0.002/img; $29 credit | Excellent (math) | 33 | Yes | Yes | Yes | STEM math/chemistry→LaTeX |
| Veryfi [55] | Remote | Proprietary | 100 docs/mo free; $0.08–0.16/doc | Excellent (vendor) | 39 | Yes | No | Yes | Receipts/invoices at scale |
| Taggun [56] | Remote | Proprietary | $28/mo+; ~$0.04–0.06/scan | Good | 205 | Limited | No | Limited | Receipt field extraction |

*Gemini is API-only but Google offers regional/Vertex deployment, not true self-host.

### (ii) Cloud-API pricing (per 1,000 pages, low-volume tier)

| Service | Raw OCR / 1k pages | Structured (forms/tables) / 1k | Free tier |
|---|---|---|---|
| Google Cloud Vision [22] | $1.50 | n/a (use Document AI) | 1,000 units/mo |
| Google Document AI [23] | $1.50 (Enterprise OCR) | $30 (Form Parser / Custom) | $300 trial credit |
| AWS Textract [24] | $1.50 | $50 forms; $70 forms+tables+queries | 3-mo: 1,000 pg/mo |
| AWS Rekognition DetectText [25] | ~$1.00 (per image) | n/a | 1,000 img/mo (12-mo) |
| Azure AI Vision Read [26] | ~$1.00–1.50 | n/a (use Document Intelligence) | 5,000 txns/mo (F0) |
| Azure Document Intelligence [27] | $1.50 (Read) | $10 Layout; $30 custom | 500 pg/mo (F0, 2-pg cap) |
| Azure DI Read OCR [42] | $1.50 | n/a | 500 pg/mo (F0) |
| OCR.space [30] | $0 (free) / flat $30–60/mo | n/a | 25,000 req/mo |
| Mistral OCR [36] | $2.00 ($1.00 batch) | +$3 annotation/1k | No standing free tier |
| Mathpix [49] | ~$2.00 (img) / $5.00 (PDF pg) | included | $29 credit |
| Mindee [26] | ~$10–100 (credit/page) | included | 250 pg/mo |
| Reducto [31] | ~$15 ($0.015/credit·page) | 2–4 credits/page | 15,000 credits |
| Unstructured.io [35] | $30 ($0.03/page) | included | 15,000 pg |
| olmOCR (self-host) [16] | ~$0.20 (~$190/M pages) | included | Free OSS + your GPU |

---

## 5. Recommended implementation roadmap for `ocracy`

### Wave 1 — implement first (the shortlist; map to scope)

| Backend | Local/Remote | Cost | Scope it covers |
|---|---|---|---|
| **tesseract** [1] | Local | Free | The dependable default; word boxes + confidence + hOCR. *(already the worked example)* |
| **paddleocr** [3] | Both | Free | High-accuracy multilingual + math + tables + handwriting + reading order; the OSS power tool. |
| **easyocr** [2] | Local | Free | Friction-free pip-only multilingual; no system binary, no GPU required. |
| **rapidocr** [6] | Local | Free | Fast ONNX path = PaddleOCR accuracy without the PaddlePaddle install. |
| **ocrmac** [14] | Local | Free | Zero-dependency on-device OCR for the (Mac-based) maintainer and macOS users. |
| **google-vision** [22] | Remote | Paid (1k free/mo) | Gold-standard cloud baseline; broad languages + handwriting + boxes/confidence. |
| **azure-document-intelligence** [27] | Remote | Paid | Tables + key-value + layout; the structured-extraction representative (alt: aws-textract [24]). |
| **mistral-ocr** [36] | Remote | Paid (cheap) | Commodity VLM: Markdown + math + tables + handwriting at $1–2/1k — the "modern OCR" slot. |
| **mathpix** [49] | Remote | Paid (cheap) | Beyond-text: best-in-class math/LaTeX + chemistry + handwriting. |
| **pix2tex** [50] | Local | Free | Free local math fallback so "read formulas" works offline with no key. |

This Wave covers every required axis: **local** (tesseract, paddleocr, easyocr, rapidocr, ocrmac, pix2tex), **remote** (google-vision, azure-di, mistral-ocr, mathpix), **free** (6) and **paid** (4), plus **math** (mathpix/pix2tex/paddleocr/mistral), **tables** (paddleocr/azure-di/mistral), and **handwriting** (google-vision/mathpix/mistral). It exercises the full `OcrResult` surface: classical engines populate boxes/confidence; VLM/Mathpix backends populate `markdown`; all populate `text`.

### Wave 2 — strong second-round candidates

- **surya** [9] / **trocr-handwritten** [47] — a local VLM (tables+math+91 languages) and a local English-handwriting recognizer, completing the "beyond-text, offline" story.
- **aws-textract** [24] — second structured-IDP cloud (if Azure DI is chosen in Wave 1) for AWS-native users.
- **olmocr** [16] or **mineru** [20] — the self-hosted bulk-PDF-to-Markdown power backend for GPU users (RAG corpora).
- **docling** [20] — if `ocracy` ever wants a document-ETL output mode (it already wraps several Wave-1 engines, so it composes naturally).
- **table-transformer** [43] / **img2table** [44] / **camelot** [45] — dedicated table extraction, where `img2table` is especially interesting as a *composition* target since it already multiplexes OCR backends.

### Leave in the ledger (catalog rows only, `implemented=False`)

The remaining ~40 records ship as discoverable, comparable rows but no facade — justified by maturity, redundancy, or niche scope:

- **Legacy / dormant:** OCRopus [13] (archived), MMOCR [8] (2023), keras-ocr [12], Nougat [21], Tabula [46], ABBYY Cloud OCR SDK [28] (end-of-sale).
- **Redundant with Wave 1:** docTR [4], OnnxTR [5], winocr [15] (covered by easyocr/rapidocr/ocrmac), Marker [20] (Datalab — surya covers it), GOT-OCR2.0 [10] (overtaken).
- **Heavy VLM zoo (GPU-only, redundant with mistral/paddleocr-VL):** DeepSeek-OCR [19], dots.ocr [18], Qwen-VL [40], InternVL [41], MiniCPM-V [40], Llama 3.2 Vision [40], GPT-4o [37], Claude [38], Gemini [39] — implement on demand.
- **Niche IDP / vertical SaaS:** Mindee [26], Nanonets [33], Klippa [29], Reducto [31], Extend [34], Upstage [30], Adobe Extract [32], LlamaParse [30], Unstructured [35], Veryfi [55], Taggun [56], OCR.space [30], Pen2Txt [54], AWS Rekognition [25].
- **DH/historical (train-your-own-model):** Kraken [11], Calamari [11], OCR4all [21].

Keep each row dated and re-verify volatile fields (pricing, model versions, leaderboard positions) periodically — the field churns on a monthly cadence.

---

## REFERENCES

1. [Tesseract (pytesseract / tesserocr)](https://github.com/tesseract-ocr/tesseract)
2. [EasyOCR — Jaided AI](https://github.com/JaidedAI/EasyOCR)
3. [PaddleOCR (PP-OCRv5 / PaddleOCR-VL)](https://github.com/PaddlePaddle/PaddleOCR)
4. [docTR — Mindee / t2k](https://github.com/mindee/doctr)
5. [OnnxTR](https://github.com/felixdittrich92/OnnxTR)
6. [RapidOCR](https://github.com/RapidAI/RapidOCR)
7. [TrOCR — Microsoft Research](https://huggingface.co/docs/transformers/model_doc/trocr)
8. [MMOCR — OpenMMLab](https://github.com/open-mmlab/mmocr)
9. [Surya OCR — Datalab](https://github.com/datalab-to/surya)
10. [GOT-OCR2.0](https://github.com/Ucas-HaoranWei/GOT-OCR2.0)
11. [Kraken ATR Engine](https://github.com/mittagessen/kraken) · [Calamari OCR](https://github.com/Calamari-OCR/calamari)
12. [Keras-OCR](https://github.com/faustomorales/keras-ocr)
13. [OCRopus / ocropy (archived)](https://github.com/ocropus-archive/DUP-ocropy)
14. [ocrmac (Apple Vision wrapper)](https://github.com/straussmaximilian/ocrmac)
15. [winocr (Windows OCR wrapper)](https://github.com/GitHub30/winocr)
16. [olmOCR — Allen Institute for AI](https://github.com/allenai/olmocr)
17. [owocr (multi-engine aggregator)](https://github.com/AuroraWright/owocr)
18. [dots.ocr — rednote-hilab](https://github.com/rednote-hilab/dots.ocr)
19. [DeepSeek-OCR](https://github.com/deepseek-ai/DeepSeek-OCR)
20. [MinerU — OpenDataLab](https://github.com/opendatalab/MinerU) · [Docling — IBM / LF AI](https://github.com/docling-project/docling) · [Marker — Datalab](https://github.com/datalab-to/marker)
21. [Nougat — Meta AI](https://github.com/facebookresearch/nougat) · [OCR4all](https://github.com/OCR4all/OCR4all)
22. [Google Cloud Vision API — OCR](https://cloud.google.com/vision/docs/ocr)
23. [Google Cloud Document AI](https://docs.cloud.google.com/document-ai/docs/enterprise-document-ocr)
24. [AWS Textract](https://aws.amazon.com/textract/pricing/)
25. [AWS Rekognition DetectText](https://docs.aws.amazon.com/rekognition/latest/dg/text-detection.html)
26. [Azure AI Vision Read OCR](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/overview-ocr) · [Mindee](https://www.mindee.com/pricing)
27. [Azure AI Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview)
28. [ABBYY Cloud OCR SDK / Document AI API](https://www.abbyy.com/ai-document-processing/api/)
29. [Klippa DocHorizon OCR API](https://www.klippa.com/en/ocr/ocr-api/)
30. [OCR.space API](https://ocr.space/ocrapi) · [Upstage Document Parse](https://www.upstage.ai/products/document-parse) · [LlamaParse — LlamaIndex](https://developers.llamaindex.ai/llamaparse/general/pricing/)
31. [Reducto](https://reducto.ai/pricing)
32. [Adobe PDF Extract API](https://developer.adobe.com/document-services/docs/overview/pdf-extract-api/)
33. [Nanonets](https://nanonets.com/ocr-api)
34. [Extend (CrowdView)](https://www.extend.ai/)
35. [Unstructured.io](https://docs.unstructured.io/api-reference/api-services/overview)
36. [Mistral OCR API (Document AI)](https://mistral.ai/news/mistral-ocr)
37. [OpenAI GPT-4o / GPT-4.1 Vision](https://developers.openai.com/api/docs/guides/images)
38. [Anthropic Claude Vision](https://platform.claude.com/docs/en/docs/build-with-claude/vision)
39. [Google Gemini Vision](https://ai.google.dev/gemini-api/docs/vision)
40. [Qwen2.5/3-VL — Alibaba](https://github.com/QwenLM/Qwen3-VL) · [MiniCPM-V — OpenBMB](https://github.com/OpenBMB/MiniCPM-V) · [Llama 3.2 Vision — Meta](https://huggingface.co/meta-llama/Llama-3.2-11B-Vision-Instruct)
41. [InternVL — OpenGVLab](https://github.com/OpenGVLab/InternVL)
42. [Azure AI Document Intelligence — Read OCR](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/read)
43. [Microsoft Table Transformer (TATR)](https://github.com/microsoft/table-transformer)
44. [img2table](https://github.com/xavctn/img2table)
45. [Camelot](https://github.com/camelot-dev/camelot)
46. [Tabula / tabula-py](https://github.com/chezou/tabula-py)
47. [TrOCR (handwritten checkpoints)](https://huggingface.co/microsoft/trocr-large-handwritten)
48. [PaddleOCR 3.0 / PP-StructureV3](https://arxiv.org/abs/2507.05595)
49. [Mathpix (Snip + Convert API)](https://mathpix.com/convert)
50. [pix2tex / LaTeX-OCR](https://github.com/lukas-blecher/LaTeX-OCR)
51. [Texify / Surya LaTeX OCR](https://github.com/VikParuchuri/texify)
52. [Google Cloud Vision — Handwriting](https://cloud.google.com/vision/docs/handwriting)
53. [OmniDocBench](https://github.com/opendatalab/OmniDocBench)
54. [Pen2Txt](https://pen2txt.com/)
55. [Veryfi OCR API](https://www.veryfi.com/receipt-ocr-api/)
56. [Taggun Receipt OCR](https://www.taggun.io/)
