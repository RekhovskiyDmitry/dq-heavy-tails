#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 6: Article-level digest for MOEX DQ/DR + tail-index research.

Reads outputs from:
  - Stage 4 tail-index estimation
  - Stage 2 DQ/DR rolling regressions
  - Stage 5 alpha-conditioned regressions

Produces compact, article-ready diagnostic tables and a memo.

Example:
python moex_stage6_article_digest.py \
  --tail-dir moex_tail_stage4_main_shares_raw \
  --stage2-dir moex_stage2_alpha_windows_shares_parallel \
  --stage5-dir moex_stage5_alpha_windows_shares_parallel \
  --outdir moex_stage6_article_digest
"""

import argparse
import os
from pathlib import Path
import numpy as np
import pandas as pd


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def q(x, p):
    return pd.Series(x).quantile(p)


def safe_read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return pd.read_csv(path)


def summarize_tail_alpha(alpha: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w, d in alpha.groupby("window"):
        rows.append({
            "window": w,
            "n_estimates": len(d),
            "n_securities": d["secid"].nunique(),
            "alpha_mean": d["alpha_consensus"].mean(),
            "alpha_median": d["alpha_consensus"].median(),
            "alpha_p10": q(d["alpha_consensus"], 0.10),
            "alpha_p25": q(d["alpha_consensus"], 0.25),
            "alpha_p75": q(d["alpha_consensus"], 0.75),
            "alpha_p90": q(d["alpha_consensus"], 0.90),
            "point_alpha_lt1": int((d["alpha_consensus"] < 1).sum()),
            "point_alpha_1_2": int(((d["alpha_consensus"] >= 1) & (d["alpha_consensus"] < 2)).sum()),
            "point_alpha_gt2": int((d["alpha_consensus"] >= 2).sum()),
            "strict_alpha_lt1": int((d["tail_group"] == "strict_alpha_lt_1").sum()),
            "strict_alpha_1_2": int((d["tail_group"] == "strict_alpha_1_2").sum()),
            "strict_alpha_gt2": int((d["tail_group"] == "strict_alpha_gt_2").sum()),
            "mean_p_alpha_lt1": d["p_alpha_lt_1"].mean(),
            "mean_p_alpha_gt2": d["p_alpha_gt_2"].mean(),
        })
    return pd.DataFrame(rows).sort_values("window")


def summarize_latest_groups(latest: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for w, d in latest.groupby("window"):
        groups = d["tail_group"].value_counts().to_dict()
        rows.append({
            "window": w,
            "n_securities": d["secid"].nunique(),
            "alpha_median": d["alpha_consensus"].median(),
            "alpha_p10": q(d["alpha_consensus"], 0.10),
            "alpha_p25": q(d["alpha_consensus"], 0.25),
            "alpha_p75": q(d["alpha_consensus"], 0.75),
            "point_alpha_lt1": int((d["alpha_consensus"] < 1).sum()),
            "point_alpha_1_2": int(((d["alpha_consensus"] >= 1) & (d["alpha_consensus"] < 2)).sum()),
            "point_alpha_gt2": int((d["alpha_consensus"] >= 2).sum()),
            "strict_alpha_lt1": groups.get("strict_alpha_lt_1", 0),
            "strict_alpha_1_2": groups.get("strict_alpha_1_2", 0),
            "strict_alpha_gt2": groups.get("strict_alpha_gt_2", 0),
            "point_alpha_1_2_uncertain": groups.get("point_alpha_1_2_uncertain", 0),
            "point_alpha_gt_2_uncertain": groups.get("point_alpha_gt_2_uncertain", 0),
            "point_alpha_lt_1_uncertain": groups.get("point_alpha_lt_1_uncertain", 0),
            "mean_p_alpha_lt1": d["p_alpha_lt_1"].mean(),
            "mean_p_alpha_gt2": d["p_alpha_gt_2"].mean(),
        })
    return pd.DataFrame(rows).sort_values("window")


def summarize_stage2_horserace(reg2: pd.DataFrame) -> pd.DataFrame:
    # compact evidence count table for DQ/DR predictive regressions
    rows = []
    params = ["dq_es", "dr_es_concentration"]
    specs = ["dq_only", "dr_only", "dq_dr", "dq_dr_current_es", "full"]
    for dep in sorted(reg2["dependent"].dropna().unique()):
        for spec in specs:
            for param in params:
                d = reg2[(reg2["dependent"] == dep) & (reg2["spec_name"] == spec) & (reg2["param"] == param)]
                if d.empty:
                    continue
                rows.append({
                    "dependent": dep,
                    "spec_name": spec,
                    "param": param,
                    "n_models": len(d),
                    "sig10": int((d["pvalue_hac"] < 0.10).sum()),
                    "sig5": int((d["pvalue_hac"] < 0.05).sum()),
                    "pos_sig10": int(((d["pvalue_hac"] < 0.10) & (d["coef"] > 0)).sum()),
                    "neg_sig10": int(((d["pvalue_hac"] < 0.10) & (d["coef"] < 0)).sum()),
                    "median_coef": d["coef"].median(),
                    "median_t_hac": d["t_hac"].median(),
                    "mean_r2": d["r2"].mean(),
                })
    return pd.DataFrame(rows)


def extract_stage2_main_table(reg2: pd.DataFrame) -> pd.DataFrame:
    # rows most likely to appear in a paper: future_tail_event, DQ/DR horse-race
    keep_specs = ["dq_only", "dr_only", "dq_dr", "dq_dr_current_es", "full"]
    d = reg2[
        (reg2["dependent"] == "future_tail_event") &
        (reg2["param"].isin(["dq_es", "dr_es_concentration"])) &
        (reg2["spec_name"].isin(keep_specs))
    ].copy()
    return d.sort_values(["period", "window", "horizon", "tail_prob", "spec_name", "param"])


def summarize_stage5_interactions(reg5: pd.DataFrame) -> pd.DataFrame:
    rows = []
    d0 = reg5[(reg5["status"] == "ok") & (reg5["param"].isin(["z_dq_x_heavy", "z_dr_x_heavy"]))].copy()
    for dep in sorted(d0["dependent"].dropna().unique()):
        for spec in sorted(d0["spec"].dropna().unique()):
            for param in ["z_dq_x_heavy", "z_dr_x_heavy"]:
                d = d0[(d0["dependent"] == dep) & (d0["spec"] == spec) & (d0["param"] == param)]
                if d.empty:
                    continue
                rows.append({
                    "dependent": dep,
                    "spec": spec,
                    "param": param,
                    "n_models": len(d),
                    "sig10": int((d["pvalue_hac"] < 0.10).sum()),
                    "sig5": int((d["pvalue_hac"] < 0.05).sum()),
                    "pos_sig10": int(((d["pvalue_hac"] < 0.10) & (d["coef"] > 0)).sum()),
                    "neg_sig10": int(((d["pvalue_hac"] < 0.10) & (d["coef"] < 0)).sum()),
                    "median_coef": d["coef"].median(),
                    "median_t_hac": d["t_hac"].median(),
                    "mean_r2": d["r2"].mean(),
                    "min_pvalue": d["pvalue_hac"].min(),
                })
    return pd.DataFrame(rows)


def key_correlations(linked: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "dq_es", "dr_es_concentration",
        "alpha_median", "alpha_q25",
        "alpha_heaviness_inv", "alpha_heaviness_below2", "alpha_heaviness_q25_below2",
        "p_alpha_gt_2_mean", "p_alpha_lt_1_mean",
        "future_tail_event", "future_es", "future_mdd", "future_rv_ann"
    ]
    rows = []
    for (period, window, horizon, tail_prob), d in linked.groupby(["period", "window", "horizon", "tail_prob"]):
        existing = [c for c in cols if c in d.columns]
        corr = d[existing].corr(numeric_only=True)
        pairs = [
            ("dq_es", "alpha_heaviness_inv"),
            ("dq_es", "alpha_median"),
            ("dr_es_concentration", "alpha_heaviness_inv"),
            ("dq_es", "dr_es_concentration"),
            ("dq_es", "future_tail_event"),
            ("dr_es_concentration", "future_tail_event"),
            ("alpha_heaviness_inv", "future_tail_event"),
            ("p_alpha_gt_2_mean", "future_tail_event"),
        ]
        for a, b in pairs:
            val = np.nan
            if a in corr.index and b in corr.columns:
                val = corr.loc[a, b]
            rows.append({
                "period": period, "window": window, "horizon": horizon, "tail_prob": tail_prob,
                "var1": a, "var2": b, "corr": val, "n_obs": len(d)
            })
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, max_rows=20) -> str:
    if df is None or df.empty:
        return "_No rows._"
    d = df.head(max_rows).copy()
    return d.to_markdown(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tail-dir", required=True)
    ap.add_argument("--stage2-dir", required=True)
    ap.add_argument("--stage5-dir", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()

    tail_dir = Path(args.tail_dir)
    stage2_dir = Path(args.stage2_dir)
    stage5_dir = Path(args.stage5_dir)
    outdir = Path(args.outdir)
    ensure_dir(outdir)

    alpha = safe_read_csv(tail_dir / "03_tail_alpha_estimates.csv")
    latest = safe_read_csv(tail_dir / "06_group_membership_latest.csv")
    reg2 = safe_read_csv(stage2_dir / "04_stage2_regressions_hac.csv")
    roll2 = safe_read_csv(stage2_dir / "02_stage2_rolling_metrics.csv")
    reg5 = safe_read_csv(stage5_dir / "02_alpha_interaction_regressions.csv")
    linked = safe_read_csv(stage5_dir / "01_alpha_linked_rolling_metrics.csv")

    tail_summary = summarize_tail_alpha(alpha)
    latest_summary = summarize_latest_groups(latest)
    stage2_summary = summarize_stage2_horserace(reg2)
    stage2_main = extract_stage2_main_table(reg2)
    stage5_summary = summarize_stage5_interactions(reg5)
    corr_summary = key_correlations(linked)

    tail_summary.to_csv(outdir / "01_tail_alpha_summary.csv", index=False)
    latest_summary.to_csv(outdir / "02_latest_tail_group_summary.csv", index=False)
    stage2_summary.to_csv(outdir / "03_stage2_horserace_summary.csv", index=False)
    stage2_main.to_csv(outdir / "04_stage2_future_tail_event_main_table.csv", index=False)
    stage5_summary.to_csv(outdir / "05_stage5_interaction_summary.csv", index=False)
    corr_summary.to_csv(outdir / "06_key_correlations.csv", index=False)

    # concise memo
    strict_lt1_total = int(tail_summary["strict_alpha_lt1"].sum())
    point_lt1_total = int(tail_summary["point_alpha_lt1"].sum())
    strict_gt2_total = int(tail_summary["strict_alpha_gt2"].sum())
    n_alpha = int(tail_summary["n_estimates"].sum())
    n_sec = int(alpha["secid"].nunique())

    dq_tail = stage2_summary[
        (stage2_summary["dependent"] == "future_tail_event") &
        (stage2_summary["param"] == "dq_es")
    ]
    dr_tail = stage2_summary[
        (stage2_summary["dependent"] == "future_tail_event") &
        (stage2_summary["param"] == "dr_es_concentration")
    ]
    inter_tail = stage5_summary[
        (stage5_summary["dependent"] == "future_tail_event") &
        (stage5_summary["param"].isin(["z_dq_x_heavy", "z_dr_x_heavy"]))
    ]

    memo = f"""# Stage 6 article digest

## Inputs
- Tail directory: `{tail_dir}`
- Stage 2 directory: `{stage2_dir}`
- Stage 5 directory: `{stage5_dir}`

## Tail-index status

The Stage 4 tail-index run contains **{n_alpha:,} rolling estimates** for **{n_sec} equities**.

- Strict alpha < 1 observations: **{strict_lt1_total:,}**
- Point alpha < 1 observations: **{point_lt1_total:,}**
- Strict alpha > 2 observations: **{strict_gt2_total:,}**

### Tail alpha summary by window

{md_table(tail_summary)}

### Latest group summary by window

{md_table(latest_summary)}

## Stage 2 DQ/DR horse-race summary

This table counts how often each signal is significant across the Stage 2 model grid.

{md_table(stage2_summary[stage2_summary['dependent'].eq('future_tail_event')])}

## Stage 5 alpha-interaction summary

This table counts significant DQ/DR × tail-heaviness interaction terms across the Stage 5 model grid.

{md_table(inter_tail, max_rows=40)}

## Key correlations

High correlations between DQ and alpha-heaviness indicate that interaction models are likely collinear and should be interpreted cautiously.

{md_table(corr_summary[corr_summary['var1'].eq('dq_es') & corr_summary['var2'].isin(['alpha_heaviness_inv', 'alpha_median', 'dr_es_concentration'])].head(30), max_rows=30)}

## Suggested interpretation

1. Conservative EVT classification does not find defensible alpha < 1 regimes among liquid MOEX equities.
2. Stage 2 provides stronger evidence that DQ predicts future tail events than that DQ predicts continuous realized ES/VaR/RV/MDD.
3. Stage 5 interaction regressions should be treated as robustness rather than the core result because DQ is highly correlated with tail-heaviness measures.
4. The article should not claim that DQ outperforms DR specifically at alpha < 1 on MOEX equities; the data do not contain that regime.
5. A defensible contribution is: DQ has predictive content for future tail-event incidence in liquid MOEX equities, while ultra-heavy alpha < 1 regimes are empirically rare under conservative EVT inference.
"""
    (outdir / "research_stage6_article_digest_memo.md").write_text(memo, encoding="utf-8")
    print(f"Wrote outputs to {outdir}")


if __name__ == "__main__":
    main()

