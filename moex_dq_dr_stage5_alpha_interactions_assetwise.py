#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 5 assetwise: robust alpha-conditioned DQ vs DR tests.

This fixes the common-date matching issue in the earlier Stage 5 script:
instead of selecting one alpha window_end for the whole portfolio date, it
matches each asset to its own latest alpha estimate with the same window and
market at or before the rolling portfolio date, within max-align-days.

Inputs:
  --rolling Stage2 02_stage2_rolling_metrics.csv
  --alpha   Stage4 03_tail_alpha_estimates.csv or stage4_tail_alpha_estimates_partial.csv
Outputs:
  00_stage5_config.json
  01_alpha_linked_rolling_metrics.csv
  02_alpha_interaction_regressions.csv
  03_alpha_bin_summary.csv
  04_alpha_signal_correlations.csv
  research_stage5_alpha_interactions_memo.md
"""

from __future__ import annotations

import argparse
import json
import math
from bisect import bisect_right
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm


DEPENDENTS_DEFAULT = ["future_tail_event", "future_es", "future_var", "future_rv_ann", "future_mdd"]
BASE_CONTROLS = ["current_es", "current_rv_ann"]


def read_table(path: str) -> pd.DataFrame:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    if p.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(p)
    return pd.read_csv(p)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def parse_assets(x) -> List[str]:
    if pd.isna(x):
        return []
    return [a.strip() for a in str(x).split(",") if a.strip()]


def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    sd = s.std(ddof=0)
    if not np.isfinite(sd) or sd == 0:
        return s * np.nan
    return (s - s.mean()) / sd


def safe_mean(x) -> float:
    s = pd.to_numeric(pd.Series(x), errors="coerce")
    return float(s.mean()) if s.notna().any() else np.nan


def safe_q(x, q) -> float:
    s = pd.to_numeric(pd.Series(x), errors="coerce").dropna()
    return float(s.quantile(q)) if len(s) else np.nan


def prepare_alpha_asset_lookup(alpha: pd.DataFrame):
    required = {"market", "secid", "window", "window_end", "alpha_consensus"}
    missing = required - set(alpha.columns)
    if missing:
        raise ValueError(f"alpha table missing columns: {sorted(missing)}")
    a = alpha.copy()
    a["market"] = a["market"].astype(str)
    a["secid"] = a["secid"].astype(str)
    a["window"] = a["window"].astype(int)
    a["window_end"] = pd.to_datetime(a["window_end"])
    a = a.sort_values(["market", "window", "secid", "window_end"])
    # one dataframe per (market, window, secid)
    out: Dict[Tuple[str, int, str], Tuple[List[pd.Timestamp], pd.DataFrame]] = {}
    for (m, w, secid), g in a.groupby(["market", "window", "secid"], sort=False):
        gg = g.drop_duplicates("window_end", keep="last").sort_values("window_end")
        dates = [pd.Timestamp(x) for x in gg["window_end"].tolist()]
        out[(str(m), int(w), str(secid))] = (dates, gg.reset_index(drop=True))
    return out


def latest_asset_alpha(asset_lookup, market: str, window: int, secid: str, target: pd.Timestamp, max_align_days: int):
    item = asset_lookup.get((str(market), int(window), str(secid)))
    if item is None:
        return None
    dates, df = item
    idx = bisect_right(dates, target) - 1
    if idx < 0:
        return None
    dt = dates[idx]
    lag = (target - dt).days
    if lag < 0 or lag > max_align_days:
        return None
    row = df.iloc[idx]
    return row, lag


def aggregate_assetwise(row: pd.Series, asset_lookup, max_align_days: int) -> dict:
    market = str(row["market"])
    window = int(row["window"])
    target = pd.Timestamp(row["tradedate"])
    assets = parse_assets(row["assets"])
    recs = []
    lags = []
    for secid in assets:
        hit = latest_asset_alpha(asset_lookup, market, window, secid, target, max_align_days)
        if hit is None:
            continue
        r, lag = hit
        recs.append(r)
        lags.append(lag)
    if not recs:
        return {
            "alpha_n_assets_total": len(assets),
            "alpha_n_assets_matched": 0,
            "alpha_match_ratio": 0.0,
            "alpha_lag_days_mean": np.nan,
            "alpha_lag_days_max": np.nan,
        }
    g = pd.DataFrame(recs)
    alpha = pd.to_numeric(g["alpha_consensus"], errors="coerce")
    out = {
        "alpha_n_assets_total": len(assets),
        "alpha_n_assets_matched": int(alpha.notna().sum()),
        "alpha_match_ratio": float(alpha.notna().sum() / max(1, len(assets))),
        "alpha_lag_days_mean": float(np.mean(lags)) if lags else np.nan,
        "alpha_lag_days_max": float(np.max(lags)) if lags else np.nan,
        "alpha_mean": safe_mean(alpha),
        "alpha_median": safe_q(alpha, 0.50),
        "alpha_q10": safe_q(alpha, 0.10),
        "alpha_q25": safe_q(alpha, 0.25),
        "alpha_min": float(alpha.min()) if alpha.notna().any() else np.nan,
        "alpha_share_lt1_point": float((alpha < 1.0).mean()) if alpha.notna().any() else np.nan,
        "alpha_share_1_2_point": float(((alpha >= 1.0) & (alpha < 2.0)).mean()) if alpha.notna().any() else np.nan,
        "alpha_share_gt2_point": float((alpha > 2.0).mean()) if alpha.notna().any() else np.nan,
    }
    for col in ["p_alpha_lt_1", "p_alpha_gt_2", "theta_runs", "zero_share_window", "max_loss_window"]:
        if col in g.columns:
            out[f"{col}_mean"] = safe_mean(g[col])
            out[f"{col}_median"] = safe_q(g[col], 0.50)
    if "tail_group" in g.columns:
        tg = g["tail_group"].astype(str)
        denom = len(tg)
        for name in [
            "strict_alpha_lt_1",
            "strict_alpha_1_2",
            "strict_alpha_gt_2",
            "point_alpha_1_2_uncertain",
            "point_alpha_gt_2_uncertain",
            "point_alpha_lt_1_uncertain",
        ]:
            out[f"share_{name}"] = float((tg == name).sum() / denom) if denom else np.nan
    return out


def link_alpha_assetwise(
    rolling: pd.DataFrame,
    alpha: pd.DataFrame,
    max_align_days: int = 45,
    min_match_ratio: float = 0.8,
) -> pd.DataFrame:
    r = rolling.copy()
    r["tradedate"] = pd.to_datetime(r["tradedate"])
    if "assets" not in r.columns:
        raise ValueError("rolling table must contain 'assets' column")
    asset_lookup = prepare_alpha_asset_lookup(alpha)
    rows = []
    cache = {}
    for _, row in r.iterrows():
        ckey = (str(row["market"]), int(row["window"]), pd.Timestamp(row["tradedate"]), str(row["assets"]))
        if ckey not in cache:
            cache[ckey] = aggregate_assetwise(row, asset_lookup, max_align_days=max_align_days)
        rows.append(cache[ckey])
    out = pd.concat([r.reset_index(drop=True), pd.DataFrame(rows)], axis=1)
    out = out[out["alpha_match_ratio"].fillna(0) >= min_match_ratio].copy()
    out["alpha_heaviness_inv"] = 1.0 / out["alpha_median"].replace(0, np.nan)
    out["alpha_heaviness_below2"] = np.maximum(0.0, 2.0 - out["alpha_median"])
    out["alpha_heaviness_q25_below2"] = np.maximum(0.0, 2.0 - out["alpha_q25"])
    out["alpha_lightness_above2"] = np.maximum(0.0, out["alpha_median"] - 2.0)
    return out


def run_hac_ols(df: pd.DataFrame, y: str, xvars: List[str], horizon: int):
    d = df[[y] + xvars].replace([np.inf, -np.inf], np.nan).dropna()
    if len(d) < max(30, len(xvars) + 10):
        return None, None, "too_few_obs"
    X = sm.add_constant(d[xvars], has_constant="add")
    try:
        model = sm.OLS(d[y].astype(float), X.astype(float)).fit(
            cov_type="HAC",
            cov_kwds={"maxlags": max(1, int(math.ceil(int(horizon) / 21)))},
        )
    except Exception as e:
        return None, None, f"fit_error: {e}"
    tab = pd.DataFrame({
        "param": model.params.index,
        "coef": model.params.values,
        "std_err_hac": model.bse.values,
        "t_hac": model.tvalues.values,
        "pvalue_hac": model.pvalues.values,
    })
    return model, tab, "ok"


def prepare_regression_frame(g: pd.DataFrame, heaviness: str, controls: bool):
    d = g.copy()
    raw_vars = ["dq_es", "dr_es_concentration", heaviness]
    if controls:
        raw_vars += [c for c in BASE_CONTROLS if c in d.columns]
    if "p_alpha_lt_1_mean" in d.columns:
        raw_vars += ["p_alpha_lt_1_mean"]
    xvars = []
    for col in raw_vars:
        if col in d.columns:
            z = f"z_{col}"
            d[z] = zscore(d[col])
            xvars.append(z)
    if "z_dq_es" in d.columns and "z_dr_es_concentration" in d.columns and f"z_{heaviness}" in d.columns:
        d["z_dq_x_heavy"] = d["z_dq_es"] * d[f"z_{heaviness}"]
        d["z_dr_x_heavy"] = d["z_dr_es_concentration"] * d[f"z_{heaviness}"]
        xvars += ["z_dq_x_heavy", "z_dr_x_heavy"]
    return d, xvars


def regression_suite(linked, dependents, min_n, heaviness_vars=None):
    if heaviness_vars is None:
        heaviness_vars = ["alpha_heaviness_inv", "alpha_heaviness_below2", "alpha_heaviness_q25_below2"]
    results = []
    group_cols = ["market", "period", "window", "horizon", "tail_prob"]
    for keys, g in linked.groupby(group_cols, dropna=False):
        market, period, window, horizon, tail_prob = keys
        if len(g) < min_n:
            continue
        for y in dependents:
            if y not in g.columns:
                continue
            for heaviness in heaviness_vars:
                if heaviness not in g.columns:
                    continue
                for controls in [False, True]:
                    spec = f"interact_{heaviness}" + ("_controls" if controls else "")
                    d, xvars = prepare_regression_frame(g, heaviness, controls)
                    model, tab, status = run_hac_ols(d, y, xvars, int(horizon))
                    if status != "ok":
                        results.append({
                            "market": market, "period": period, "window": window, "horizon": horizon,
                            "tail_prob": tail_prob, "dependent": y, "spec": spec,
                            "status": status, "n_obs": len(d), "param": None,
                        })
                    else:
                        for _, rr in tab.iterrows():
                            results.append({
                                "market": market, "period": period, "window": window, "horizon": horizon,
                                "tail_prob": tail_prob, "dependent": y, "spec": spec,
                                "status": "ok", "n_obs": int(model.nobs), "r2": float(model.rsquared),
                                "adj_r2": float(model.rsquared_adj), "aic": float(model.aic), "bic": float(model.bic),
                                **rr.to_dict(),
                            })
    return pd.DataFrame(results)


def bin_summary(linked: pd.DataFrame, n_bins: int) -> pd.DataFrame:
    rows = []
    group_cols = ["market", "period", "window", "horizon", "tail_prob"]
    for keys, g in linked.groupby(group_cols, dropna=False):
        d = g.copy()
        if d["alpha_median"].nunique(dropna=True) < n_bins:
            continue
        try:
            d["alpha_bin"] = pd.qcut(d["alpha_median"], q=n_bins, duplicates="drop")
        except Exception:
            continue
        for b, h in d.groupby("alpha_bin", observed=True):
            rows.append({
                "market": keys[0], "period": keys[1], "window": keys[2], "horizon": keys[3], "tail_prob": keys[4],
                "alpha_bin": str(b), "n_obs": len(h),
                "alpha_median": h["alpha_median"].median(),
                "alpha_q25": h["alpha_q25"].median(),
                "dq_es_mean": h["dq_es"].mean(),
                "dr_es_concentration_mean": h["dr_es_concentration"].mean(),
                "future_tail_event_mean": h["future_tail_event"].mean() if "future_tail_event" in h.columns else np.nan,
                "future_es_mean": h["future_es"].mean() if "future_es" in h.columns else np.nan,
                "future_mdd_mean": h["future_mdd"].mean() if "future_mdd" in h.columns else np.nan,
                "p_alpha_gt_2_mean": h["p_alpha_gt_2_mean"].mean() if "p_alpha_gt_2_mean" in h.columns else np.nan,
                "p_alpha_lt_1_mean": h["p_alpha_lt_1_mean"].mean() if "p_alpha_lt_1_mean" in h.columns else np.nan,
            })
    return pd.DataFrame(rows)


def signal_correlations(linked: pd.DataFrame) -> pd.DataFrame:
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
    rows = []
    for keys, g in linked.groupby(["market", "period", "window", "horizon", "tail_prob"], dropna=False):
        for a, b in pairs:
            if a in g.columns and b in g.columns:
                val = g[[a, b]].replace([np.inf, -np.inf], np.nan).dropna().corr().iloc[0, 1]
            else:
                val = np.nan
            rows.append({
                "market": keys[0], "period": keys[1], "window": keys[2], "horizon": keys[3], "tail_prob": keys[4],
                "var1": a, "var2": b, "corr": val, "n_obs": len(g),
            })
    return pd.DataFrame(rows)


def md_table(df, max_rows=20):
    if df is None or df.empty:
        return "_No rows._"
    return df.head(max_rows).to_markdown(index=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rolling", required=True)
    ap.add_argument("--alpha", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--markets", nargs="+", default=["shares"])
    ap.add_argument("--periods", nargs="+", default=None)
    ap.add_argument("--windows", nargs="+", type=int, default=None)
    ap.add_argument("--horizons", nargs="+", type=int, default=None)
    ap.add_argument("--tail-probs", nargs="+", type=float, default=None)
    ap.add_argument("--max-align-days", type=int, default=45)
    ap.add_argument("--min-match-ratio", type=float, default=0.8)
    ap.add_argument("--min-n", type=int, default=50)
    ap.add_argument("--dependents", nargs="+", default=DEPENDENTS_DEFAULT)
    ap.add_argument("--n-bins", type=int, default=4)
    ap.add_argument("--n-jobs", type=int, default=1, help="Accepted for CLI compatibility; computation is sequential.")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    ensure_dir(outdir)

    rolling = read_table(args.rolling)
    alpha = read_table(args.alpha)

    rolling["market"] = rolling["market"].astype(str)
    rolling = rolling[rolling["market"].isin(args.markets)].copy()
    if args.periods:
        rolling = rolling[rolling["period"].isin(args.periods)].copy()
    if args.windows:
        rolling = rolling[rolling["window"].astype(int).isin(args.windows)].copy()
    if args.horizons:
        rolling = rolling[rolling["horizon"].astype(int).isin(args.horizons)].copy()
    if args.tail_probs:
        rolling = rolling[rolling["tail_prob"].astype(float).isin(args.tail_probs)].copy()

    linked = link_alpha_assetwise(
        rolling=rolling,
        alpha=alpha,
        max_align_days=args.max_align_days,
        min_match_ratio=args.min_match_ratio,
    )

    reg = regression_suite(linked, dependents=args.dependents, min_n=args.min_n)
    bins = bin_summary(linked, n_bins=args.n_bins)
    corr = signal_correlations(linked)

    (outdir / "00_stage5_config.json").write_text(json.dumps(vars(args), indent=2, ensure_ascii=False))
    linked.to_csv(outdir / "01_alpha_linked_rolling_metrics.csv", index=False)
    reg.to_csv(outdir / "02_alpha_interaction_regressions.csv", index=False)
    bins.to_csv(outdir / "03_alpha_bin_summary.csv", index=False)
    corr.to_csv(outdir / "04_alpha_signal_correlations.csv", index=False)

    periods = linked["period"].value_counts().to_dict() if not linked.empty else {}
    summary_rows = []
    if not reg.empty:
        tmp = reg[(reg["status"] == "ok") & (reg["param"].isin(["z_dq_x_heavy", "z_dr_x_heavy"]))]
        for (dep, spec, param), d in tmp.groupby(["dependent", "spec", "param"]):
            summary_rows.append({
                "dependent": dep, "spec": spec, "param": param,
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
    sumdf = pd.DataFrame(summary_rows)

    memo = []
    memo.append("# Stage 5 assetwise alpha interactions memo\n")
    memo.append("## Inputs\n")
    memo.append(f"- rolling: `{args.rolling}`\n")
    memo.append(f"- alpha: `{args.alpha}`\n")
    memo.append("\n## Linked rows\n")
    memo.append(f"- rows: {len(linked):,}\n")
    memo.append(f"- periods: {periods}\n")
    if not linked.empty:
        memo.append(f"- match ratio min/median/max: {linked['alpha_match_ratio'].min():.3f} / {linked['alpha_match_ratio'].median():.3f} / {linked['alpha_match_ratio'].max():.3f}\n")
        memo.append(f"- lag days mean/max: {linked['alpha_lag_days_mean'].mean():.2f} / {linked['alpha_lag_days_max'].max():.0f}\n")
        memo.append(f"- median portfolio alpha: {linked['alpha_median'].median():.3f}\n")
        if "p_alpha_lt_1_mean" in linked.columns:
            memo.append(f"- mean P(alpha<1): {linked['p_alpha_lt_1_mean'].mean():.6f}\n")
        if "p_alpha_gt_2_mean" in linked.columns:
            memo.append(f"- mean P(alpha>2): {linked['p_alpha_gt_2_mean'].mean():.6f}\n")
    memo.append("\n## Interaction summary\n")
    memo.append(md_table(sumdf, max_rows=80))
    memo.append("\n\n## Note\n")
    memo.append("This version uses assetwise nearest alpha matching. It is preferred when Stage 4 produces sparse per-security window_end dates.\n")
    (outdir / "research_stage5_alpha_interactions_memo.md").write_text("".join(memo), encoding="utf-8")


if __name__ == "__main__":
    main()
