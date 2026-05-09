# CalliRAG

Plan A data-preparation and retrieval-validation repository for a zero-training Chinese calligraphy retrieval experiment.

This repository focuses on one question:

> Can structure-aware retrieval select useful real Wang Xizhi reference glyphs, and can those references improve FontDiffuser generation when used only through the existing style-reference channel?

It does not train a model, modify FontDiffuser, add adapters, or implement a full RAG generator. Adapter/model work belongs in the separate `FontDiffuser-retrieval` repository.

## Scope

- Single-character generation.
- Single calligrapher: Wang Xizhi.
- Traditional Chinese target characters.
- Candidate target pool currently contains 15 manually selected cases.
- The final experiment set can later be reduced to 12 cases after inspection.
- Retrieval is rule-based and uses IDS/layout/component metadata.
- Layer 1 validates retrieval quality.
- Layer 2 validates FontDiffuser generation with retrieved references.

## Repository Layout

```text
callirag/
  bank/
    raw/                         # original OCR/decomposition bank data
    bank_enriched.json            # derived retrieval metadata
    non_trivial_components.json    # component ontology used by retrieval

  cases/
    case_assets_15.csv             # 15-case candidate asset index
    wxz_gt_chars.csv               # legacy 8-case list

  quick_eva/                       # main Plan A 11-step pipeline
  legacy_pipeline/                 # old scripts kept for reference only

  outputs/
    case_manifest.csv              # formal case list used by current run
    layer1/                        # retrieval-level validation outputs
    layer2/                        # generation-level validation manifests/results
    legacy/                        # old/cache/temp outputs; not for normal use
```

## Main Pipeline

Run from the parent workspace root, for example `D:/htt`:

```bash
python callirag/quick_eva/build_case_manifest.py
python callirag/quick_eva/build_non_trivial_components.py
python callirag/quick_eva/build_bank_enriched.py
python callirag/quick_eva/bank_coverage_check.py
python callirag/quick_eva/retrieve_structural.py
python callirag/quick_eva/export_layer1_visuals.py
python callirag/quick_eva/analyze_layer1.py
python callirag/quick_eva/build_experiment_manifest.py
python callirag/quick_eva/run_fontdiffuser_batch.py
python callirag/quick_eva/build_blind_pairs.py
python callirag/quick_eva/analyze_layer2.py
```

Or run all steps:

```bash
python callirag/quick_eva/run_all.py
```

Notes:

- `run_fontdiffuser_batch.py` is dry-run by default. Use `--execute` only when ready to call FontDiffuser.
- `analyze_layer1.py` and `analyze_layer2.py` create annotation templates when labels are missing.
- `outputs/case_manifest.csv` is the authoritative case list for a run. `cases/case_assets_15.csv` is only the larger candidate pool.

## Output Policy

Keep small, reproducible experiment metadata in Git:

- `bank/raw/*.json`
- `bank/raw/*.csv`
- `bank_enriched.json`
- `non_trivial_components.json`
- `cases/*.csv`
- `outputs/case_manifest.csv`
- `outputs/layer1/*.csv`
- `outputs/layer1/*.json`
- `outputs/layer1/layer1_visuals/*.md`
- `outputs/layer2/*.csv`
- `quick_eva/*.py`
- `legacy_pipeline/*.py`

Do not commit heavy or machine-specific files:

- generated images
- content/baseline image assets
- checkpoints
- local environments
- `outputs/legacy/`
- bulk inference folders such as `generation_outputs/` and `blind_images/`

If a large file is needed to reproduce a run, document where it came from instead of committing it.

## Git Rules

Before creating the new GitHub repository, make sure this folder is a fresh repository with clean authorship:

```bash
cd D:/htt/callirag
git init
git status
git config user.name
git config user.email
```

If `user.name` or `user.email` is not your own identity, set it for this repository only:

```bash
git config user.name "Your Name"
git config user.email "your-email@example.com"
```

Rules:

- Do not reuse old Git history if the old repository has unwanted contributors.
- Do not use `git push --mirror`.
- Do not force-push unless you intentionally recreate the repository.
- Do not commit `.env`, credentials, checkpoints, generated images, or local environment folders.
- Keep Plan A data processing in this repository.
- Keep adapter/model integration work in `FontDiffuser-retrieval`.

## New GitHub Upload Steps

Recommended flow when the old GitHub repository is already named `callirag`:

1. Rename the old GitHub repository to `callirag-archive`.
2. Create a new empty GitHub repository named `callirag`.
3. Initialize this local folder as a new repository:

```bash
cd D:/htt/callirag
git init
git add README.md .gitignore
git add bank cases quick_eva legacy_pipeline outputs/case_manifest.csv outputs/layer1 outputs/layer2
git status
git commit -m "Initialize CalliRAG Plan A repository"
```

4. Connect the new remote:

```bash
git branch -M main
git remote add origin git@github.com:<your-user-or-org>/callirag.git
git push -u origin main
```

5. After pushing, check GitHub contributors. It should show only the author identity used for the new initial commit.

If you prefer not to rename the old repository, create the new repository under another name, such as `callirag-planA`.
