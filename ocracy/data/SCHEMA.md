# ocracy ledger schema (`backends.json`)

The ledger is the data-driven gallery of OCR backends ocracy knows about —
**whether or not** a working facade ships for them. It lives in
`ocracy/data/backends.json` (data, not code) so it can be curated, filtered,
diffed, and extended without touching Python. `ocracy.catalog` reads it.

Top-level shape:

```json
{ "meta": { "as_of": "2026-06", "schema_version": 1 }, "backends": [ { …record… } ] }
```

(A bare top-level array `[ {record}, … ]` is also accepted.)

## Record fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable kebab-case id, the catalog key (e.g. `google-vision`). |
| `name` | string | Human name. |
| `vendor` | string | Company / maintainer. |
| `homepage` | string | Project or product URL. |
| `deployment` | string | Comma-joined of: `python_lib`, `cli`, `rest_api`, `sdk`, `desktop_app`, `vlm_api`, `self_hostable`. |
| `is_local` | bool | Can run fully on the user's machine. |
| `is_remote` | bool | Offered as a hosted API/service. (Both may be true.) |
| `open_source` | bool | Source-available under an OSI-ish license. |
| `license` | string | SPDX-ish id, or `proprietary`. |
| `pricing_model` | enum | `free_oss`, `pay_as_you_go`, `subscription`, `freemium`, `free_tier_then_paid`, `proprietary_quote`, `mixed`. |
| `price_note` | string | Concrete current price + unit + as-of period. |
| `free_tier` | string | What you get for free. |
| `languages_count` | int\|null | Documented language count, if any. |
| `languages_note` | string | Scripts/families (Latin, CJK, Arabic, Cyrillic, Indic…). Free-text; filterable by substring. |
| `handwriting` | enum | `yes` / `limited` / `no` / `unknown`. |
| `math_formula` | enum | Math/LaTeX recognition. |
| `tables` | enum | Table-structure extraction. |
| `layout_structure` | enum | Reading order / regions / document structure. |
| `output_formats` | string[] | e.g. `text`, `hocr`, `alto`, `json_bbox`, `pdf`, `markdown`, `latex`, `docx`. |
| `bounding_boxes` | bool | Returns word/line geometry. |
| `confidence_scores` | bool | Returns per-unit confidence. |
| `gpu_recommended` | enum | `yes` / `optional` / `no` / `na` (local engines). |
| `accuracy_tier` | enum | `excellent` / `good` / `fair` / `varies` / `unknown`. |
| `accuracy_note` | string | Benchmark numbers (OmniDocBench/OCRBench/CER/WER) + source. |
| `speed_note` | string | Throughput/latency notes. |
| `maturity_note` | string | Stars, last release, active? (as-of date). |
| `privacy_note` | string | Does data leave the machine? on-prem option? |
| `beyond_text` | string[] | Non-plain-text capabilities: `math`, `tables`, `handwriting`, `barcodes`, `music`, `key_value`, `charts`, `signatures`. Filterable. |
| `best_for` | string | One-line "reach for this when…". |
| `python_install` | string | `pip install …`, or `N/A — REST only`. |
| `api_env_var` | string | Credential env var(s) for remote backends, else `""`. |
| `pros` | string[] | Decision-relevant upsides. |
| `cons` | string[] | Decision-relevant downsides. |
| `citations` | string[] | Source URLs. |
| `confidence` | enum | Researcher confidence in this record: `high` / `medium` / `low`. |

## Computed (not stored)

| Field | Meaning |
|---|---|
| `implemented` | Whether ocracy ships a working facade — computed **live** from the registry (a real `ocracy/backends/<id>/` exists), so it never drifts from the JSON. |
