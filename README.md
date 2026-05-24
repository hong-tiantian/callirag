# CalliRAG — Plan A

Zero-training **structure-aware reference selection + two-layer validation** for Chinese calligraphy generation (VQ-Font-inspired; no FontDiffuser model changes).

---

## What this experiment does

**Core question:**

> Can IDS / layout / structural components retrieve real Wang Xizhi calligraphy references that help fine-grained target structure—and when those references are used only as FontDiffuser **style references**, does generation improve?

**Out of scope (this repo):**

- Model training, UNet changes, adapters, full RAG fusion  
- See the separate `FontDiffuser-retrieval` repo for that work

**In scope:**

| Layer | Question | Runs FontDiffuser? |
|-------|----------|-------------------|
| **Layer 1** | Does the bank contain structurally relevant exemplars? Is structural ranking better than random? | No |
| **Layer 2** | Do rank 1 / 3 / 5 retrieved references improve fine-grained structure as style refs? | Yes (style ref only) |

**Layer 2 groups:**

| Group | Name | Reference source |
|-------|------|------------------|
| A | `fixed_baseline` | Fixed 「永」 (`cases/style_wxz1175.jpg`) |
| B | `uniform_random` | Uniform random from valid bank (5 seeds) |
| C | `structural_top1` | Structural retrieval rank 1 |
| D | `rank_ablation` | Structural retrieval rank 3 / rank 5 |

**15 target cases** — authoritative list: `outputs/case_manifest.csv` (manually selected after baseline inspection).

---

## Repository layout

```text
callirag/
├── README.md
├── pipeline/                     # All scripts (prep + plan)
│   ├── common.py                 # Paths, CSV/JSON helpers
│   ├── run_all.py                # Run plan_01 … plan_11 in order
│   ├── prep_01 … prep_05         # Group A: one-time Wang Xizhi bank build
│   └── plan_01 … plan_12         # Group B: Plan A main flow (12 = optional OCR)
│
├── assets/                       # IDS / Unihan sources (gitignored; not part of bank/)
│   ├── ids.txt, ids_full.txt
│   └── Unihan_*.txt
│
├── bank/                         # tracked in Git
│   ├── raw/
│   │   ├── wxz_ocr.json
│   │   ├── decomp.json
│   │   └── wxz_bank.json
│   ├── bank_enriched.json
│   └── non_trivial_components.json
│
├── cases/                        # tracked in Git (15-case assets + images)
│   ├── case_assets_15.csv
│   ├── style_wxz1175.jpg         # Group A fixed style ref
│   ├── content/                  # FontDiffuser content images
│   ├── baseline/                 # Baseline generations
│   └── gt/                       # Target GT images
│
├── outputs/                      # tracked in Git (CSVs / JSON / MD)
│   ├── case_manifest.csv
│   ├── layer1/
│   └── layer2/
│
└── metrics/                      # gitignored — local annotation / OCR workspace
```

---

## Pipeline scripts

Prefix indicates group:

### Group A — `prep_*` (one-time bank build)

| Script | Role | Main output |
|--------|------|-------------|
| `prep_01_ocr_wxz.py` | OCR on Wang Xizhi images | `bank/raw/wxz_ocr.json` |
| `prep_02_decompose.py` | IDS recursive decomposition | `bank/raw/decomp.json` |
| `prep_03_buildbank.py` | Merge OCR + decomposition | `bank/raw/wxz_bank.json` |
| `prep_04_build_retrieval.py` | Build `retrieval_components` | updates `wxz_bank.json` |
| `prep_05_generate_content_images.py` | Content images (optional) | `cases/content/{id}.jpg` |

### Group B — `plan_*` (Plan A main flow)

| Step | Script | Layer | Main output |
|------|--------|-------|-------------|
| 01 | `plan_01_build_case_manifest.py` | — | `outputs/case_manifest.csv` |
| 02 | `plan_02_build_non_trivial_components.py` | — | `bank/non_trivial_components.json` |
| 03 | `plan_03_build_bank_enriched.py` | — | `bank/bank_enriched.json` |
| 04 | `plan_04_bank_coverage_check.py` | L1 | `outputs/layer1/bank_coverage.csv` |
| 05 | `plan_05_retrieve_structural.py` | L1 | `sim_layer.json`, `retrieval_topk_manifest.csv` |
| 06 | `plan_06_export_layer1_visuals.py` | L1 | `layer1_visuals/*.md` |
| 07 | `plan_07_analyze_layer1.py` | L1 | `layer1_results.csv` |
| 08 | `plan_08_build_experiment_manifest.py` | L2 | `experiment_manifest.csv` |
| 09 | `plan_09_run_fontdiffuser_batch.py` | L2 | `generation_outputs/` |
| 10 | `plan_10_build_blind_pairs.py` | L2 | `blind_eval_pairs.csv`, etc. |
| 11 | `plan_11_analyze_layer2.py` | L2 | `layer2_results.csv` |
| 12 | `plan_12_analyze_layer2_ocr.py` | L2 | `metrics/layer2_ocr_*.csv` (optional) |

---

## How to run

From the workspace root (e.g. clone parent repo or set `PYTHONPATH` accordingly):

### One-time bank build

```bash
python callirag/pipeline/prep_01_ocr_wxz.py
python callirag/pipeline/prep_02_decompose.py
python callirag/pipeline/prep_03_buildbank.py
python callirag/pipeline/prep_04_build_retrieval.py
python callirag/pipeline/prep_05_generate_content_images.py   # optional
```

### Plan A main flow (step by step)

```bash
python callirag/pipeline/plan_01_build_case_manifest.py
python callirag/pipeline/plan_02_build_non_trivial_components.py
python callirag/pipeline/plan_03_build_bank_enriched.py
python callirag/pipeline/plan_04_bank_coverage_check.py
python callirag/pipeline/plan_05_retrieve_structural.py
python callirag/pipeline/plan_06_export_layer1_visuals.py
python callirag/pipeline/plan_07_analyze_layer1.py
python callirag/pipeline/plan_08_build_experiment_manifest.py
python callirag/pipeline/plan_09_run_fontdiffuser_batch.py
python callirag/pipeline/plan_10_build_blind_pairs.py
python callirag/pipeline/plan_11_analyze_layer2.py
```

### Run all plan steps

```bash
python callirag/pipeline/run_all.py
```

**Notes:**

- `plan_09` is **dry-run by default** (writes `run_commands.txt` only). Use `--execute` for real FontDiffuser inference.
- `plan_07` / `plan_11` create empty annotation templates if labels are missing; fill `layer1_annotation.csv` / `layer2_annotation.csv` and rerun.
- Authoritative case list: **`outputs/case_manifest.csv`**.

---

## Key outputs

### `outputs/layer1/`

| File | Description |
|------|-------------|
| `bank_coverage.csv` | Per-target bank coverage |
| `sim_layer.json` | Structural top-5 rankings (used by Layer 2 groups C/D) |
| `retrieval_topk_manifest.csv` | Structural + random top-5 details |
| `layer1_visuals/*.md` | Human review pages |
| `layer1_annotation.csv` | Layer 1 labels |
| `layer1_results.csv` | Layer 1 metrics |

### `outputs/layer2/`

| File | Description |
|------|-------------|
| `experiment_manifest.csv` | All A/B/C/D FontDiffuser tasks (135 rows) |
| `blind_eval_pairs.csv` | Blind pairwise pairs |
| `group_mapping_private.csv` | Hidden group mapping (not for evaluators) |
| `layer2_annotation.csv` | Expert blind labels |
| `layer2_results.csv` | Win rates and summaries |

Large images under `generation_outputs/`, `blind_images/`, and `blind_pair_sheets/` are gitignored.

---

## What is tracked in Git

This repository includes:

| Path | Contents |
|------|----------|
| `pipeline/` | All `prep_*` and `plan_*` scripts, `common.py`, `run_all.py` |
| `bank/` | `raw/*.json`, `bank_enriched.json`, `non_trivial_components.json` |
| `cases/` | `case_assets_15.csv`, `style_wxz1175.jpg`, `content/`, `baseline/`, `gt/` |
| `outputs/` | `case_manifest.csv`, `layer1/*`, `layer2/*.csv` and related metadata |

**Gitignored (see `.gitignore`):**

- `metrics/` — local annotation backups and optional OCR analysis
- `assets/` — IDS / Unihan source files (download from Unicode)
- `outputs/**/generation_outputs/`, `blind_images/`, `blind_pair_sheets/` — large generated PNG/JPG batches
- `outputs/legacy/`, model weights, `.env`, local `data/`

Human evaluation screenshots and multi-rater labels can live in a report appendix; they are not required in this repo.

---

## Related repos

| Repo | Role |
|------|------|
| **callirag** (this) | Data prep, structural retrieval, two-layer validation |
| **FontDiffuser** | Base generator |
| **FontDiffuser-retrieval** | Adapter / retrieval fusion (outside Plan A) |

---

## Suggested report wording

> We conduct a two-layer validation of structure-aware reference selection for Chinese calligraphy generation. Layer 1 evaluates whether the Wang Xizhi bank and rule-based ranking return fine-detail-relevant exemplars. Layer 2 tests whether rank 1/3/5 retrieved references improve FontDiffuser outputs when used only as style references, without model modification.
