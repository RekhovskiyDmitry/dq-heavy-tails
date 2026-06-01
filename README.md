# DQ Heavy Tails

Research project for a coursework paper on Diversification Quotient (DQ), Diversification Ratio (DR), and heavy-tailed risk in MOEX equities.

## Current Research Claim

The first audit changes the central empirical framing.

The available Stage4 estimates do **not** support a strong claim that liquid MOEX equities contain a defensible `alpha < 1` regime: strict `alpha < 1` observations are zero in the current conservative EVT classification.

The defensible article claim is narrower:

> DQ contains predictive information about future tail-event incidence beyond the classical DR. DQ is strongly connected with portfolio tail-heaviness, but alpha-conditioned interaction models should be interpreted cautiously because DQ and tail-heaviness are highly correlated.

## Repository Layout

```text
pipeline/
  moex_tail_index_stage4.py
  moex_tail_index_stage4_db_checkpoint.py
  moex_dq_dr_stage2_robustness_parallel.py
  moex_dq_dr_stage5_alpha_interactions_assetwise.py
  moex_stage6_article_digest.py
  moex_heavy_tails_pipeline.py

article/
  figures/                     # first-pass article candidate figures

docs/
  AUDIT_2026-06-01.md           # first-pass audit and research direction
```

The repository still contains legacy archives, raw dumps, notebooks, and generated output folders in the root. They are intentionally not deleted in this first cleanup pass because the canonical reproducibility bundle must be chosen before history is rewritten or large files are removed from GitHub.

## Core Empirical Artifacts

The best current article bundle is `moex_article_core_assetwise_20260524_1008.zip`. It contains:

- Stage4 tail-index estimates for 142 MOEX equities.
- Stage2 rolling DQ/DR metrics and HAC regressions.
- Stage5 assetwise alpha-matched interaction regressions.
- Stage6 digest tables and memo.

The root-level extracted folders are incomplete compared with this assetwise bundle.

## First-Pass Figures

Candidate figures are in `article/figures/`:

- `01_alpha_distribution_by_window.png`
- `02_latest_tail_group_counts.png`
- `03_dq_dr_alpha_timeseries.png`
- `04_dq_vs_alpha_median.png`
- `05_dq_dr_boxplot_by_alpha_q25_group.png`
- `06_stage2_tail_event_significance.png`

These are exploratory but already useful for selecting the final result section.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Rebuild Stage6 Digest From the Assetwise Bundle

Unpack the article bundle into a local working directory:

```bash
mkdir -p data/raw
unzip moex_article_core_assetwise_20260524_1008.zip -d data/raw
```

Then rebuild the digest:

```bash
python pipeline/moex_stage6_article_digest.py \
  --tail-dir data/raw/moex_article_core_bundle_assetwise/moex_tail_stage4_main_shares_raw \
  --stage2-dir data/raw/moex_article_core_bundle_assetwise/moex_stage2_alpha_windows_shares_parallel \
  --stage5-dir data/raw/moex_article_core_bundle_assetwise/moex_stage5_alpha_windows_shares_assetwise \
  --outdir article/stage6_digest
```

## Next Cleanup Tasks

1. Decide whether the assetwise bundle is the canonical reproducibility bundle.
2. Remove or quarantine raw dumps and intermediate archives from the visible working tree.
3. If the repository must be slim on GitHub, rewrite Git history with a deliberate large-file cleanup.
4. Verify the exact DQ formula against the primary DQ paper before finalizing the theory section.
5. Rewrite the draft around the empirical result rather than around the unsupported `alpha < 1` claim.
