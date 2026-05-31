#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOEX heavy tails / DQ vs DR exploratory pipeline.

What it does:
1) Loads daily log returns from PostgreSQL table moex_daily_returns.
2) Runs data-quality diagnostics for all assets.
3) Computes per-security distribution and tail diagnostics.
4) Builds coverage-based research universes for shares and bonds.
5) Runs rolling equal-weight portfolio DQ/DR diagnostics.
6) Tests whether current DQ/DR predict future ES / VaR / volatility / drawdown.
7) Writes CSV tables, PNG figures and a markdown research memo.

Designed for the schema:
id, secid, boardid, market, tradedate, ..., log_return, ...

Minimum required columns: secid, market, tradedate, log_return.
Optional but useful: boardid.

Author: ChatGPT research assistant
Date: 2026-05-17
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    import matplotlib.pyplot as plt
except Exception as exc:  # pragma: no cover
    plt = None
    print(f"[WARN] matplotlib is unavailable: {exc}", file=sys.stderr)

try:
    from sqlalchemy import create_engine, inspect, text
except Exception as exc:  # pragma: no cover
    create_engine = None
    inspect = None
    text = None
    print(f"[ERROR] sqlalchemy is required: {exc}", file=sys.stderr)

try:
    from scipy import stats
except Exception as exc:  # pragma: no cover
    stats = None
    print(f"[WARN] scipy is unavailable. Some tests will be skipped: {exc}", file=sys.stderr)

try:
    import statsmodels.api as sm
    from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch
except Exception as exc:  # pragma: no cover
    sm = None
    acorr_ljungbox = None
    het_arch = None
    print(f"[WARN] statsmodels is unavailable. Regressions/diagnostics will be skipped: {exc}", file=sys.stderr)


# -----------------------------
# Configuration
# -----------------------------

@dataclass
class Config:
    db_url: str
    table: str
    schema: Optional[str]
    outdir: Path
    start_date: Optional[str]
    end_date: Optional[str]
    tail_prob: float
    min_obs: int
    min_coverage: float
    max_abs_log_return_flag: float
    rolling_window: int
    future_horizon: int
    rolling_step: int
    min_assets_window: int
    max_assets_per_market: int
    min_complete_rows_ratio: float
    run_rolling: bool
    run_security_tests: bool
    diagnostic_sample_max: int
    random_seed: int


# -----------------------------
# Generic utilities
# -----------------------------

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def safe_to_csv(df: pd.DataFrame, path: Path, index: bool = False) -> None:
    ensure_dir(path.parent)
    df.to_csv(path, index=index, encoding="utf-8-sig")
    print(f"[WRITE] {path}")


def safe_json_dump(obj: dict, path: Path) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)
    print(f"[WRITE] {path}")


def annualize_vol(x: pd.Series) -> float:
    return float(x.std(ddof=1) * np.sqrt(252)) if x.notna().sum() > 1 else np.nan


def max_drawdown_from_returns(r: pd.Series) -> float:
    """Max drawdown from log returns. Returns positive drawdown magnitude."""
    r = pd.Series(r).dropna()
    if len(r) == 0:
        return np.nan
    wealth = np.exp(r.cumsum())
    peak = wealth.cummax()
    dd = wealth / peak - 1.0
    return float(-dd.min())


def var_loss(losses: Sequence[float], tail_prob: float = 0.025) -> float:
    """
    Historical VaR for positive losses at tail probability p.
    p=0.025 corresponds to 97.5% confidence.
    """
    arr = np.asarray(losses, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan
    return float(np.quantile(arr, 1.0 - tail_prob, method="linear"))


def es_loss(losses: Sequence[float], tail_prob: float = 0.025) -> float:
    """
    Historical expected shortfall for positive losses at tail probability p.
    Uses the mean of the largest ceil(p*n) losses.
    """
    arr = np.asarray(losses, dtype=float)
    arr = arr[np.isfinite(arr)]
    n = len(arr)
    if n == 0:
        return np.nan
    k = int(max(1, math.ceil(tail_prob * n)))
    largest = np.partition(arr, n - k)[n - k:]
    return float(np.mean(largest))


def hill_tail_index_from_losses(losses: Sequence[float], k: Optional[int] = None) -> float:
    """
    Hill estimator for Pareto tail index alpha, using positive losses.
    Larger losses are more extreme. Returns alpha = 1 / gamma_hat.

    Important: this is a rough diagnostic, not a final publishable EVT procedure.
    For a paper, validate k with sensitivity analysis / Hill plots.
    """
    x = np.asarray(losses, dtype=float)
    x = x[np.isfinite(x)]
    x = x[x > 0]
    n = len(x)
    if n < 30:
        return np.nan
    x = np.sort(x)
    if k is None:
        k = int(max(10, min(np.sqrt(n), 0.1 * n)))
    k = int(k)
    if k < 2 or k >= n:
        return np.nan
    threshold = x[-k - 1]
    if threshold <= 0:
        return np.nan
    top = x[-k:]
    gamma_hat = np.mean(np.log(top) - np.log(threshold))
    if gamma_hat <= 0 or not np.isfinite(gamma_hat):
        return np.nan
    return float(1.0 / gamma_hat)


def hill_tail_index_multi(losses: Sequence[float], ks: Sequence[int]) -> Dict[str, float]:
    out = {}
    for k in ks:
        out[f"hill_alpha_k_{k}"] = hill_tail_index_from_losses(losses, k=k)
    return out


def empirical_dr_es(returns_window: pd.DataFrame, weights: np.ndarray, tail_prob: float) -> float:
    """
    ES concentration ratio in the spirit of user's DR formula:
        DR_ES = ES(portfolio) / sum_i w_i ES(asset_i)
    Lower values imply stronger diversification. Values near 1 imply weak diversification.
    """
    x = returns_window.dropna(axis=0, how="any").to_numpy(dtype=float)
    if x.ndim != 2 or x.shape[0] < 30 or x.shape[1] != len(weights):
        return np.nan
    w = np.asarray(weights, dtype=float)
    port_ret = x @ w
    port_es = es_loss(-port_ret, tail_prob=tail_prob)
    comp_es = np.array([es_loss(-x[:, j], tail_prob=tail_prob) for j in range(x.shape[1])])
    denom = float(np.dot(w, comp_es))
    if denom <= 0 or not np.isfinite(denom):
        return np.nan
    return float(port_es / denom)


def empirical_dq_es(
    returns_window: pd.DataFrame,
    weights: np.ndarray,
    tail_prob: float = 0.025,
    grid_size: int = 250,
    max_tail_prob: float = 0.50,
) -> float:
    """
    Empirical ES-based DQ prototype.

    Interpretation used here:
    - risk parameter is tail probability p, not confidence 1-p;
    - ES_p is the mean of the worst p fraction of losses;
    - beta* is the smallest tail probability beta such that
          ES_beta(portfolio) <= sum_i w_i ES_alpha(asset_i),
      where alpha = tail_prob;
    - DQ = beta* / alpha.

    If diversification is strong, beta* can be much smaller than alpha, so DQ is near 0.
    If diversification is weak, beta* is close to alpha, so DQ is near 1.
    If sample/subadditivity issues appear, DQ may exceed 1.

    This is a practical empirical inversion. Before journal submission, validate it against
    the exact notation used in Han-Lin-Zhao (2025) and replicate one example from the paper.
    """
    x = returns_window.dropna(axis=0, how="any").to_numpy(dtype=float)
    if x.ndim != 2 or x.shape[0] < 60 or x.shape[1] != len(weights):
        return np.nan

    w = np.asarray(weights, dtype=float)
    port_ret = x @ w
    comp_es = np.array([es_loss(-x[:, j], tail_prob=tail_prob) for j in range(x.shape[1])])
    standalone_sum = float(np.dot(w, comp_es))
    if standalone_sum <= 0 or not np.isfinite(standalone_sum):
        return np.nan

    n = len(port_ret)
    min_tail_prob = max(1.0 / n, 1e-4)
    max_tail_prob = max(max_tail_prob, tail_prob * 1.25)
    max_tail_prob = min(max_tail_prob, 0.95)

    # ES_beta decreases as beta increases under tail-probability parameterization.
    grid = np.linspace(min_tail_prob, max_tail_prob, grid_size)
    es_grid = np.array([es_loss(-port_ret, tail_prob=b) for b in grid])
    ok = np.where(es_grid <= standalone_sum)[0]
    if len(ok) == 0:
        return np.nan
    beta_star = float(grid[ok[0]])
    return float(beta_star / tail_prob)


def clean_returns(df: pd.DataFrame, cfg: Config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    df["tradedate"] = pd.to_datetime(df["tradedate"])
    df["secid"] = df["secid"].astype(str).str.strip()
    df["market"] = df["market"].astype(str).str.strip().str.lower()
    if "boardid" in df.columns:
        df["boardid"] = df["boardid"].astype(str).str.strip()

    df["log_return"] = pd.to_numeric(df["log_return"], errors="coerce")

    if cfg.start_date:
        df = df[df["tradedate"] >= pd.Timestamp(cfg.start_date)]
    if cfg.end_date:
        df = df[df["tradedate"] <= pd.Timestamp(cfg.end_date)]

    df["is_nonfinite_return"] = ~np.isfinite(df["log_return"])
    df["is_extreme_return_flag"] = df["log_return"].abs() > cfg.max_abs_log_return_flag

    duplicates = df[df.duplicated(subset=["secid", "market", "tradedate"], keep=False)].copy()

    # If duplicates exist, aggregate by mean return; for article we will later inspect duplicated cases.
    group_cols = ["secid", "market", "tradedate"]
    if "boardid" in df.columns:
        # Keep boardid only if unique; otherwise join boards into a string for diagnostics.
        board_map = (
            df.groupby(group_cols)["boardid"]
            .apply(lambda s: ",".join(sorted(set(s.dropna().astype(str)))))
            .reset_index()
        )
    else:
        board_map = None

    df_clean = (
        df.loc[~df["is_nonfinite_return"], group_cols + ["log_return"]]
        .groupby(group_cols, as_index=False)["log_return"]
        .mean()
    )
    if board_map is not None:
        df_clean = df_clean.merge(board_map, on=group_cols, how="left")

    bad_rows = pd.concat(
        [
            df[df["is_nonfinite_return"]].assign(problem="nonfinite_log_return"),
            df[df["is_extreme_return_flag"]].assign(problem="extreme_abs_log_return"),
            duplicates.assign(problem="duplicate_secid_market_date"),
        ],
        ignore_index=True,
        sort=False,
    )
    return df_clean, bad_rows


# -----------------------------
# Loading data
# -----------------------------

def load_data(cfg: Config) -> pd.DataFrame:
    if create_engine is None:
        raise RuntimeError("sqlalchemy is not available")
    engine = create_engine(cfg.db_url)
    insp = inspect(engine)

    table_name = cfg.table
    schema = cfg.schema

    cols_available = [c["name"] for c in insp.get_columns(table_name, schema=schema)]
    required = ["secid", "market", "tradedate", "log_return"]
    missing = [c for c in required if c not in cols_available]
    if missing:
        raise ValueError(f"Required columns are missing from {table_name}: {missing}")

    columns = ["secid", "market", "tradedate", "log_return"]
    if "boardid" in cols_available:
        columns.insert(2, "boardid")

    col_sql = ", ".join(columns)
    full_table = f"{schema}.{table_name}" if schema else table_name
    where_clauses = []
    params = {}
    if cfg.start_date:
        where_clauses.append("tradedate >= :start_date")
        params["start_date"] = cfg.start_date
    if cfg.end_date:
        where_clauses.append("tradedate <= :end_date")
        params["end_date"] = cfg.end_date
    where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    sql = text(f"SELECT {col_sql} FROM {full_table} {where_sql}")
    print(f"[LOAD] {full_table}: {col_sql}")
    df = pd.read_sql(sql, engine, params=params)
    print(f"[LOAD] rows={len(df):,}, secids={df['secid'].nunique():,}")
    return df


# -----------------------------
# Diagnostics
# -----------------------------

def dataset_overview(df_raw: pd.DataFrame, df_clean: pd.DataFrame, bad_rows: pd.DataFrame) -> pd.DataFrame:
    records = []
    for name, d in [("raw", df_raw), ("clean", df_clean)]:
        records.append(
            {
                "dataset": name,
                "rows": len(d),
                "secids": d["secid"].nunique() if "secid" in d else np.nan,
                "markets": ", ".join(sorted(map(str, d["market"].dropna().unique()))) if "market" in d else "",
                "date_min": d["tradedate"].min() if "tradedate" in d else None,
                "date_max": d["tradedate"].max() if "tradedate" in d else None,
                "missing_log_return": int(d["log_return"].isna().sum()) if "log_return" in d else np.nan,
            }
        )
    records.append(
        {
            "dataset": "bad_rows_flags",
            "rows": len(bad_rows),
            "secids": bad_rows["secid"].nunique() if len(bad_rows) else 0,
            "markets": ", ".join(sorted(map(str, bad_rows["market"].dropna().unique()))) if len(bad_rows) else "",
            "date_min": bad_rows["tradedate"].min() if len(bad_rows) else None,
            "date_max": bad_rows["tradedate"].max() if len(bad_rows) else None,
            "missing_log_return": int(bad_rows["log_return"].isna().sum()) if len(bad_rows) else 0,
        }
    )
    return pd.DataFrame(records)


def market_date_ranges(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("market")
        .agg(
            rows=("log_return", "size"),
            secids=("secid", "nunique"),
            date_min=("tradedate", "min"),
            date_max=("tradedate", "max"),
            trading_days=("tradedate", "nunique"),
            mean_assets_per_day=("secid", lambda s: np.nan),
        )
        .reset_index()
        .drop(columns=["mean_assets_per_day"])
    )


def date_market_breadth(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["market", "tradedate"])
        .agg(secids=("secid", "nunique"), rows=("log_return", "size"), mean_return=("log_return", "mean"))
        .reset_index()
    )


def sec_coverage(df: pd.DataFrame) -> pd.DataFrame:
    market_days = df.groupby("market")["tradedate"].nunique().rename("market_trading_days").reset_index()
    out = (
        df.groupby(["market", "secid"])
        .agg(
            n_obs=("log_return", "size"),
            date_min=("tradedate", "min"),
            date_max=("tradedate", "max"),
            n_days=("tradedate", "nunique"),
            zero_return_share=("log_return", lambda x: float(np.mean(np.isclose(x, 0.0)))),
            abs_return_q99=("log_return", lambda x: float(np.nanquantile(np.abs(x), 0.99)) if len(x) else np.nan),
            abs_return_max=("log_return", lambda x: float(np.nanmax(np.abs(x))) if len(x) else np.nan),
        )
        .reset_index()
        .merge(market_days, on="market", how="left")
    )
    out["coverage_ratio_vs_market_days"] = out["n_days"] / out["market_trading_days"]
    return out.sort_values(["market", "n_obs"], ascending=[True, False])


def security_stats(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    records = []
    grouped = df.groupby(["market", "secid"], sort=False)
    n_total = grouped.ngroups
    for idx, ((market, secid), g) in enumerate(grouped, start=1):
        r = g["log_return"].dropna().astype(float)
        n = len(r)
        if n < cfg.min_obs:
            continue
        losses = -r.to_numpy()
        ks = [max(10, int(np.sqrt(n))), max(20, int(0.05 * n)), max(30, int(0.10 * n))]
        ks = sorted(set([k for k in ks if 2 < k < n]))
        rec = {
            "market": market,
            "secid": secid,
            "n_obs": n,
            "date_min": g["tradedate"].min(),
            "date_max": g["tradedate"].max(),
            "mean_daily": float(r.mean()),
            "median_daily": float(r.median()),
            "std_daily": float(r.std(ddof=1)),
            "ann_vol": annualize_vol(r),
            "skew": float(stats.skew(r, bias=False)) if stats is not None and n > 2 else np.nan,
            "excess_kurtosis": float(stats.kurtosis(r, fisher=True, bias=False)) if stats is not None and n > 3 else np.nan,
            "min_return": float(r.min()),
            "max_return": float(r.max()),
            "zero_return_share": float(np.mean(np.isclose(r, 0.0))),
            "VaR_95_loss": var_loss(losses, 0.05),
            "ES_95_loss": es_loss(losses, 0.05),
            "VaR_975_loss": var_loss(losses, 0.025),
            "ES_975_loss": es_loss(losses, 0.025),
            "max_drawdown": max_drawdown_from_returns(r),
        }
        rec.update(hill_tail_index_multi(losses, ks))
        records.append(rec)
        if idx % 500 == 0:
            print(f"[SECURITY_STATS] {idx:,}/{n_total:,} groups processed")
    return pd.DataFrame(records)


def security_tests(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Potentially expensive per-security tests. Runs on largest coverage securities plus random sample."""
    if not cfg.run_security_tests:
        return pd.DataFrame()
    if stats is None:
        print("[SKIP] scipy unavailable; security tests skipped")
        return pd.DataFrame()

    cov = sec_coverage(df)
    rng = np.random.default_rng(cfg.random_seed)
    top = cov.sort_values("n_obs", ascending=False).head(cfg.diagnostic_sample_max)
    # Add a random component, so we do not only test liquid securities.
    if len(cov) > cfg.diagnostic_sample_max:
        rand_idx = rng.choice(cov.index.to_numpy(), size=min(cfg.diagnostic_sample_max, len(cov)), replace=False)
        selected = pd.concat([top, cov.loc[rand_idx]], ignore_index=True).drop_duplicates(["market", "secid"])
    else:
        selected = cov

    selected_keys = set(zip(selected["market"], selected["secid"]))
    records = []
    for (market, secid), g in df.groupby(["market", "secid"], sort=False):
        if (market, secid) not in selected_keys:
            continue
        r = g["log_return"].dropna().astype(float)
        n = len(r)
        if n < max(cfg.min_obs, 100):
            continue
        rec = {"market": market, "secid": secid, "n_obs": n}
        try:
            jb = stats.jarque_bera(r)
            rec["jarque_bera_stat"] = float(jb.statistic)
            rec["jarque_bera_pvalue"] = float(jb.pvalue)
        except Exception:
            rec["jarque_bera_stat"] = np.nan
            rec["jarque_bera_pvalue"] = np.nan
        if acorr_ljungbox is not None:
            try:
                lb = acorr_ljungbox(r, lags=[10], return_df=True)
                rec["ljungbox_ret_lag10_pvalue"] = float(lb["lb_pvalue"].iloc[0])
                lb2 = acorr_ljungbox(r**2, lags=[10], return_df=True)
                rec["ljungbox_sqret_lag10_pvalue"] = float(lb2["lb_pvalue"].iloc[0])
            except Exception:
                rec["ljungbox_ret_lag10_pvalue"] = np.nan
                rec["ljungbox_sqret_lag10_pvalue"] = np.nan
        if het_arch is not None:
            try:
                arch = het_arch(r, nlags=10)
                rec["arch_lm_lag10_stat"] = float(arch[0])
                rec["arch_lm_lag10_pvalue"] = float(arch[1])
            except Exception:
                rec["arch_lm_lag10_stat"] = np.nan
                rec["arch_lm_lag10_pvalue"] = np.nan
        records.append(rec)
    return pd.DataFrame(records)


# -----------------------------
# Periods and universes
# -----------------------------

def make_periods(df: pd.DataFrame) -> pd.DataFrame:
    dmin = pd.Timestamp(df["tradedate"].min())
    dmax = pd.Timestamp(df["tradedate"].max())
    candidates = [
        ("full_available", dmin, dmax),
        ("pre_2020", pd.Timestamp("2014-01-01"), pd.Timestamp("2019-12-31")),
        ("covid_2020_2021", pd.Timestamp("2020-01-01"), pd.Timestamp("2021-12-31")),
        ("shock_2022_2023", pd.Timestamp("2022-01-01"), pd.Timestamp("2023-12-31")),
        ("post_2024", pd.Timestamp("2024-01-01"), dmax),
        ("baseline_2018_plus", pd.Timestamp("2018-01-01"), dmax),
    ]
    rows = []
    for name, start, end in candidates:
        start2 = max(start, dmin)
        end2 = min(end, dmax)
        if start2 <= end2:
            tmp = df[(df["tradedate"] >= start2) & (df["tradedate"] <= end2)]
            rows.append(
                {
                    "period": name,
                    "start": start2.date(),
                    "end": end2.date(),
                    "rows": len(tmp),
                    "secids": tmp["secid"].nunique(),
                    "markets": ", ".join(sorted(tmp["market"].unique())),
                    "trading_days": tmp["tradedate"].nunique(),
                }
            )
    return pd.DataFrame(rows)


def period_stats_by_market(df: pd.DataFrame) -> pd.DataFrame:
    periods = make_periods(df)
    rows = []
    for _, p in periods.iterrows():
        start = pd.Timestamp(p["start"])
        end = pd.Timestamp(p["end"])
        tmp = df[(df["tradedate"] >= start) & (df["tradedate"] <= end)]
        for market, g in tmp.groupby("market"):
            rows.append(
                {
                    "period": p["period"],
                    "market": market,
                    "start": start.date(),
                    "end": end.date(),
                    "rows": len(g),
                    "secids": g["secid"].nunique(),
                    "trading_days": g["tradedate"].nunique(),
                    "median_obs_per_secid": float(g.groupby("secid")["tradedate"].nunique().median()),
                    "mean_obs_per_secid": float(g.groupby("secid")["tradedate"].nunique().mean()),
                }
            )
    return pd.DataFrame(rows)


def universe_candidates(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    cov = sec_coverage(df)
    out = cov[(cov["n_obs"] >= cfg.min_obs) & (cov["coverage_ratio_vs_market_days"] >= cfg.min_coverage)].copy()
    out["coverage_rank_in_market"] = out.groupby("market")["n_obs"].rank(ascending=False, method="first")
    out["candidate_for_rolling"] = out["coverage_rank_in_market"] <= cfg.max_assets_per_market
    return out.sort_values(["market", "coverage_rank_in_market"])


# -----------------------------
# Market portfolio diagnostics
# -----------------------------

def equal_weight_market_returns(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["market", "tradedate"])
        .agg(
            ew_log_return=("log_return", "mean"),
            n_assets=("secid", "nunique"),
        )
        .reset_index()
    )


def market_portfolio_stats(ew: pd.DataFrame) -> pd.DataFrame:
    records = []
    for market, g in ew.groupby("market"):
        r = g.sort_values("tradedate")["ew_log_return"].dropna()
        losses = -r
        records.append(
            {
                "market": market,
                "n_days": len(r),
                "date_min": g["tradedate"].min(),
                "date_max": g["tradedate"].max(),
                "mean_daily": float(r.mean()),
                "ann_vol": annualize_vol(r),
                "skew": float(stats.skew(r, bias=False)) if stats is not None and len(r) > 2 else np.nan,
                "excess_kurtosis": float(stats.kurtosis(r, fisher=True, bias=False)) if stats is not None and len(r) > 3 else np.nan,
                "VaR_975_loss": var_loss(losses, 0.025),
                "ES_975_loss": es_loss(losses, 0.025),
                "hill_alpha": hill_tail_index_from_losses(losses),
                "max_drawdown": max_drawdown_from_returns(r),
                "mean_assets_per_day": float(g["n_assets"].mean()),
            }
        )
    return pd.DataFrame(records)


# -----------------------------
# Rolling DQ/DR diagnostics
# -----------------------------

def add_regime_features(dates: pd.Series) -> pd.DataFrame:
    d = pd.to_datetime(dates)
    out = pd.DataFrame({"tradedate": d})
    out["regime_pre_2020"] = (d < pd.Timestamp("2020-01-01")).astype(int)
    out["regime_covid"] = ((d >= pd.Timestamp("2020-01-01")) & (d <= pd.Timestamp("2021-12-31"))).astype(int)
    out["regime_2022_2023"] = ((d >= pd.Timestamp("2022-01-01")) & (d <= pd.Timestamp("2023-12-31"))).astype(int)
    out["regime_post_2024"] = (d >= pd.Timestamp("2024-01-01")).astype(int)
    out["near_2022_trade_break"] = ((d >= pd.Timestamp("2022-02-01")) & (d <= pd.Timestamp("2022-04-30"))).astype(int)
    return out


def rolling_portfolio_metrics_for_market(df: pd.DataFrame, market: str, cfg: Config) -> pd.DataFrame:
    g = df[df["market"] == market].copy()
    if g.empty:
        return pd.DataFrame()

    cand = universe_candidates(g, cfg)
    cand = cand[cand["candidate_for_rolling"]]
    secids = cand["secid"].head(cfg.max_assets_per_market).tolist()
    if len(secids) < cfg.min_assets_window:
        print(f"[ROLLING:{market}] skipped: only {len(secids)} candidate assets")
        return pd.DataFrame()

    pivot = (
        g[g["secid"].isin(secids)]
        .pivot_table(index="tradedate", columns="secid", values="log_return", aggfunc="mean")
        .sort_index()
    )
    dates = pivot.index.to_list()
    n_dates = len(dates)
    rows = []
    print(f"[ROLLING:{market}] pivot days={n_dates:,}, assets={pivot.shape[1]:,}")

    start_idx = cfg.rolling_window
    end_idx = n_dates - cfg.future_horizon
    if end_idx <= start_idx:
        print(f"[ROLLING:{market}] skipped: insufficient dates")
        return pd.DataFrame()

    for t in range(start_idx, end_idx, cfg.rolling_step):
        date_t = dates[t]
        win = pivot.iloc[t - cfg.rolling_window:t].copy()
        fut = pivot.iloc[t:t + cfg.future_horizon].copy()

        # Choose assets with enough observations in estimation window and future horizon.
        win_cov = win.notna().mean(axis=0)
        fut_cov = fut.notna().mean(axis=0)
        eligible = win.columns[(win_cov >= cfg.min_coverage) & (fut_cov >= cfg.min_coverage)].tolist()
        if len(eligible) < cfg.min_assets_window:
            continue

        win2 = win[eligible].dropna(axis=0, how="any")
        fut2 = fut[eligible].dropna(axis=0, how="any")
        if len(win2) < cfg.rolling_window * cfg.min_complete_rows_ratio:
            continue
        if len(fut2) < cfg.future_horizon * cfg.min_complete_rows_ratio:
            continue

        n_assets = len(eligible)
        weights = np.repeat(1.0 / n_assets, n_assets)
        win_port = pd.Series(win2.to_numpy() @ weights, index=win2.index)
        fut_port = pd.Series(fut2.to_numpy() @ weights, index=fut2.index)

        current_losses = -win_port
        future_losses = -fut_port
        rec = {
            "market": market,
            "tradedate": date_t,
            "n_assets": n_assets,
            "window_rows": len(win2),
            "future_rows": len(fut2),
            "dq_es": empirical_dq_es(win2, weights, tail_prob=cfg.tail_prob),
            "dr_es_concentration": empirical_dr_es(win2, weights, tail_prob=cfg.tail_prob),
            "current_es": es_loss(current_losses, cfg.tail_prob),
            "current_var": var_loss(current_losses, cfg.tail_prob),
            "current_rv_ann": annualize_vol(win_port),
            "current_hill_alpha": hill_tail_index_from_losses(current_losses),
            "future_es": es_loss(future_losses, cfg.tail_prob),
            "future_var": var_loss(future_losses, cfg.tail_prob),
            "future_rv_ann": annualize_vol(fut_port),
            "future_mdd": max_drawdown_from_returns(fut_port),
            "future_cum_log_return": float(fut_port.sum()),
            "future_tail_event_975": int(np.any(future_losses > var_loss(current_losses, cfg.tail_prob))),
            "assets": ",".join(eligible),
        }
        rows.append(rec)

    out = pd.DataFrame(rows)
    if not out.empty:
        regimes = add_regime_features(out["tradedate"])
        out = pd.concat([out.reset_index(drop=True), regimes.drop(columns=["tradedate"]).reset_index(drop=True)], axis=1)
    return out


def rolling_portfolio_metrics(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    if not cfg.run_rolling:
        return pd.DataFrame()
    rows = []
    for market in sorted(df["market"].dropna().unique()):
        rows.append(rolling_portfolio_metrics_for_market(df, market, cfg))
    out = pd.concat([x for x in rows if x is not None and not x.empty], ignore_index=True) if rows else pd.DataFrame()
    return out


def predictive_regressions(rolling: pd.DataFrame) -> pd.DataFrame:
    if rolling.empty or sm is None:
        return pd.DataFrame()
    y_vars = ["future_es", "future_var", "future_rv_ann", "future_mdd", "future_tail_event_975"]
    x_base = ["dq_es", "dr_es_concentration", "current_es", "current_rv_ann", "current_hill_alpha", "n_assets"]
    regime_vars = ["regime_covid", "regime_2022_2023", "regime_post_2024", "near_2022_trade_break"]
    records = []
    for market, g in rolling.groupby("market"):
        for y in y_vars:
            cols = [y] + x_base + regime_vars
            d = g[cols].replace([np.inf, -np.inf], np.nan).dropna()
            if len(d) < 30:
                continue
            X = d[x_base + regime_vars].copy()
            # Avoid collinearity if a regime dummy is all 0/1.
            X = X.loc[:, X.nunique(dropna=True) > 1]
            X = sm.add_constant(X, has_constant="add")
            Y = d[y]
            try:
                model = sm.OLS(Y, X).fit(cov_type="HAC", cov_kwds={"maxlags": 3})
            except Exception:
                model = sm.OLS(Y, X).fit()
            for param in model.params.index:
                records.append(
                    {
                        "market": market,
                        "dependent": y,
                        "n_obs": int(model.nobs),
                        "r2": float(model.rsquared),
                        "adj_r2": float(model.rsquared_adj),
                        "aic": float(model.aic),
                        "bic": float(model.bic),
                        "param": param,
                        "coef": float(model.params[param]),
                        "std_err": float(model.bse[param]),
                        "t": float(model.tvalues[param]),
                        "pvalue": float(model.pvalues[param]),
                    }
                )
    return pd.DataFrame(records)


# -----------------------------
# Figures
# -----------------------------

def save_figures(df: pd.DataFrame, sec_stats: pd.DataFrame, rolling: pd.DataFrame, outdir: Path) -> None:
    if plt is None:
        return
    figdir = outdir / "figures"
    ensure_dir(figdir)

    # Breadth over time by market.
    breadth = date_market_breadth(df)
    for market, g in breadth.groupby("market"):
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(g["tradedate"], g["secids"])
        ax.set_title(f"Number of available securities per day: {market}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Number of secids")
        fig.tight_layout()
        path = figdir / f"breadth_{market}.png"
        fig.savefig(path, dpi=150)
        plt.close(fig)
        print(f"[WRITE] {path}")

    # Tail index distribution.
    hill_cols = [c for c in sec_stats.columns if c.startswith("hill_alpha")]
    if hill_cols:
        col = hill_cols[0]
        for market, g in sec_stats.groupby("market"):
            vals = g[col].replace([np.inf, -np.inf], np.nan).dropna()
            vals = vals[(vals > 0) & (vals < vals.quantile(0.99))]
            if len(vals) < 5:
                continue
            fig, ax = plt.subplots(figsize=(8, 5))
            ax.hist(vals, bins=40)
            ax.set_title(f"Hill tail-index distribution: {market}")
            ax.set_xlabel("Hill alpha")
            ax.set_ylabel("Count")
            fig.tight_layout()
            path = figdir / f"hill_alpha_hist_{market}.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            print(f"[WRITE] {path}")

    # Rolling DQ/DR time series.
    if not rolling.empty:
        for market, g in rolling.groupby("market"):
            g = g.sort_values("tradedate")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(g["tradedate"], g["dq_es"], label="DQ ES")
            ax.plot(g["tradedate"], g["dr_es_concentration"], label="DR ES concentration")
            ax.set_title(f"Rolling DQ vs DR: {market}")
            ax.set_xlabel("Date")
            ax.set_ylabel("Metric")
            ax.legend()
            fig.tight_layout()
            path = figdir / f"rolling_dq_dr_{market}.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            print(f"[WRITE] {path}")

            fig, ax = plt.subplots(figsize=(8, 5))
            ax.scatter(g["dq_es"], g["future_es"], alpha=0.7)
            ax.set_title(f"DQ vs future ES: {market}")
            ax.set_xlabel("DQ ES")
            ax.set_ylabel("Future ES")
            fig.tight_layout()
            path = figdir / f"scatter_dq_future_es_{market}.png"
            fig.savefig(path, dpi=150)
            plt.close(fig)
            print(f"[WRITE] {path}")


def write_research_memo(
    cfg: Config,
    overview: pd.DataFrame,
    ranges: pd.DataFrame,
    sec_stats: pd.DataFrame,
    periods: pd.DataFrame,
    portfolio_stats_df: pd.DataFrame,
    rolling: pd.DataFrame,
    regressions: pd.DataFrame,
    outdir: Path,
) -> None:
    lines = []
    lines.append("# MOEX heavy tails / DQ vs DR: автоматический исследовательский меморандум")
    lines.append("")
    lines.append("## 1. Что было сделано")
    lines.append("Скрипт загрузил дневные лог-доходности из PostgreSQL, очистил нечисловые значения, агрегировал дубликаты secid-market-date и построил диагностические таблицы по акциям и облигациям.")
    lines.append("")
    lines.append("## 2. Общий размер данных")
    lines.append(overview.to_markdown(index=False))
    lines.append("")
    lines.append("## 3. Доступные рынки и периоды")
    lines.append(ranges.to_markdown(index=False))
    lines.append("")
    lines.append("## 4. Предлагаемые периоды анализа")
    lines.append(periods.to_markdown(index=False))
    lines.append("")
    lines.append("Рабочее решение: основной период выбирать автоматически как максимально длинный интервал с достаточным покрытием, но обязательно делать robustness отдельно для 2018+, 2020–2021, 2022–2023 и 2024+.")
    lines.append("")
    lines.append("## 5. Хвосты и распределения")
    if sec_stats.empty:
        lines.append("Недостаточно наблюдений для security-level статистик.")
    else:
        summary_cols = ["market", "n_obs", "ann_vol", "excess_kurtosis", "ES_975_loss", "max_drawdown"]
        hill_cols = [c for c in sec_stats.columns if c.startswith("hill_alpha")]
        if hill_cols:
            summary_cols.append(hill_cols[0])
        summary = sec_stats.groupby("market")[summary_cols[1:]].agg(["count", "mean", "median", "min", "max"])
        lines.append(summary.to_markdown())
        lines.append("")
        lines.append("Самые тяжелые хвосты по первой Hill-оценке:")
        if hill_cols:
            col = hill_cols[0]
            tmp = sec_stats[["market", "secid", "n_obs", "ES_975_loss", "excess_kurtosis", col]].dropna().sort_values(col).head(20)
            lines.append(tmp.to_markdown(index=False))
    lines.append("")
    lines.append("## 6. Equal-weight рыночные портфели")
    if portfolio_stats_df.empty:
        lines.append("Не рассчитано.")
    else:
        lines.append(portfolio_stats_df.to_markdown(index=False))
    lines.append("")
    lines.append("## 7. Rolling DQ/DR")
    if rolling.empty:
        lines.append("Rolling-блок не был запущен или не набрал достаточно данных. Проверь --run-rolling, --min-assets-window, --min-coverage, --rolling-window.")
    else:
        agg = rolling.groupby("market")[["dq_es", "dr_es_concentration", "future_es", "future_rv_ann", "future_mdd", "n_assets"]].agg(["count", "mean", "median", "min", "max"])
        lines.append(agg.to_markdown())
        lines.append("")
        lines.append("Интерпретация: если DQ действительно работает, его высокие значения должны быть положительно связаны с future_es / future_mdd и сохранять значимость при включении DR.")
    lines.append("")
    lines.append("## 8. Прогнозные регрессии")
    if regressions.empty:
        lines.append("Регрессии не рассчитаны: либо нет rolling-таблицы, либо мало наблюдений, либо statsmodels недоступен.")
    else:
        key = regressions[regressions["param"].isin(["dq_es", "dr_es_concentration"])].copy()
        key = key.sort_values(["market", "dependent", "param"])
        lines.append(key.to_markdown(index=False))
        lines.append("")
        lines.append("Первый научный фильтр: ищем dependent=future_es и positive/significant coef для dq_es при контроле dr_es_concentration.")
    lines.append("")
    lines.append("## 9. Что смотреть в первую очередь")
    lines.append("1. `03_bad_returns.csv`: есть ли экстремальные или дублирующиеся наблюдения, которые ломают хвосты.")
    lines.append("2. `04_security_stats.csv`: распределение ES, kurtosis и Hill alpha по акциям/облигациям.")
    lines.append("3. `07_research_universe_candidates.csv`: какие secid подходят для rolling-анализа.")
    lines.append("4. `08_portfolio_rolling_metrics.csv`: ведут ли DQ и DR себя по-разному.")
    lines.append("5. `09_predictive_regressions.csv`: есть ли у DQ прогнозная сила для future ES.")
    lines.append("")
    lines.append("## 10. Предварительные направления статьи")
    lines.append("- Если DQ значим для future ES, а DR нет: статья про дополнительную прогнозную силу DQ на российском рынке.")
    lines.append("- Если DQ работает только в 2022–2023: статья про режимную зависимость диверсификации под тяжелыми хвостами.")
    lines.append("- Если акции и облигации резко отличаются: статья может стать сравнением хвостовой диверсификации по классам активов.")
    lines.append("- Если DQ и DR не отличаются: статья про эмпирические ограничения DQ на рынке с разрывами торгов и неоднородной ликвидностью.")
    lines.append("")
    lines.append("## 11. Важная методологическая оговорка")
    lines.append("Реализация ES-DQ в этом скрипте — практическая эмпирическая инверсия tail-probability параметра. Перед финальной статьей ее нужно сверить с точной формулировкой Han–Lin–Zhao и желательно воспроизвести один пример из их статьи.")

    path = outdir / "research_memo.md"
    with path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[WRITE] {path}")


# -----------------------------
# Main
# -----------------------------

def parse_args() -> Config:
    parser = argparse.ArgumentParser(description="MOEX heavy tails / DQ vs DR exploratory pipeline")
    parser.add_argument("--db-url", default="postgresql://postgres:password2544@localhost:5432/heavy_tails_data")
    parser.add_argument("--table", default="moex_total_return_daily")
    parser.add_argument("--schema", default=None)
    parser.add_argument("--outdir", default="moex_research_outputs")
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--tail-prob", type=float, default=0.025, help="0.025 = ES/VaR at 97.5% confidence")
    parser.add_argument("--min-obs", type=int, default=250)
    parser.add_argument("--min-coverage", type=float, default=0.80)
    parser.add_argument("--max-abs-log-return-flag", type=float, default=1.0)
    parser.add_argument("--rolling-window", type=int, default=252)
    parser.add_argument("--future-horizon", type=int, default=21)
    parser.add_argument("--rolling-step", type=int, default=21)
    parser.add_argument("--min-assets-window", type=int, default=10)
    parser.add_argument("--max-assets-per-market", type=int, default=80)
    parser.add_argument("--min-complete-rows-ratio", type=float, default=0.80)
    parser.add_argument("--run-rolling", action="store_true")
    parser.add_argument("--run-security-tests", action="store_true")
    parser.add_argument("--diagnostic-sample-max", type=int, default=200)
    parser.add_argument("--random-seed", type=int, default=42)
    args = parser.parse_args()

    return Config(
        db_url=args.db_url,
        table=args.table,
        schema=args.schema,
        outdir=Path(args.outdir),
        start_date=args.start_date,
        end_date=args.end_date,
        tail_prob=args.tail_prob,
        min_obs=args.min_obs,
        min_coverage=args.min_coverage,
        max_abs_log_return_flag=args.max_abs_log_return_flag,
        rolling_window=args.rolling_window,
        future_horizon=args.future_horizon,
        rolling_step=args.rolling_step,
        min_assets_window=args.min_assets_window,
        max_assets_per_market=args.max_assets_per_market,
        min_complete_rows_ratio=args.min_complete_rows_ratio,
        run_rolling=args.run_rolling,
        run_security_tests=args.run_security_tests,
        diagnostic_sample_max=args.diagnostic_sample_max,
        random_seed=args.random_seed,
    )


def main() -> None:
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    cfg = parse_args()
    ensure_dir(cfg.outdir)
    safe_json_dump(cfg.__dict__ | {"outdir": str(cfg.outdir)}, cfg.outdir / "00_config.json")

    df_raw = load_data(cfg)
    df_clean, bad_rows = clean_returns(df_raw, cfg)

    overview = dataset_overview(df_raw, df_clean, bad_rows)
    ranges = market_date_ranges(df_clean)
    breadth = date_market_breadth(df_clean)
    coverage = sec_coverage(df_clean)
    periods = make_periods(df_clean)
    period_stats = period_stats_by_market(df_clean)
    sec_stats = security_stats(df_clean, cfg)
    tests = security_tests(df_clean, cfg)
    universe = universe_candidates(df_clean, cfg)
    ew = equal_weight_market_returns(df_clean)
    ew_stats = market_portfolio_stats(ew)

    safe_to_csv(overview, cfg.outdir / "00_dataset_overview.csv")
    safe_to_csv(ranges, cfg.outdir / "01_market_date_ranges.csv")
    safe_to_csv(breadth, cfg.outdir / "02_date_market_breadth.csv")
    safe_to_csv(bad_rows, cfg.outdir / "03_bad_returns.csv")
    safe_to_csv(sec_stats, cfg.outdir / "04_security_stats.csv")
    safe_to_csv(tests, cfg.outdir / "05_security_tests_sample.csv")
    safe_to_csv(periods, cfg.outdir / "06_auto_periods.csv")
    safe_to_csv(period_stats, cfg.outdir / "06_period_stats_by_market.csv")
    safe_to_csv(universe, cfg.outdir / "07_research_universe_candidates.csv")
    safe_to_csv(ew, cfg.outdir / "07_equal_weight_market_returns.csv")
    safe_to_csv(ew_stats, cfg.outdir / "07_equal_weight_market_stats.csv")

    rolling = rolling_portfolio_metrics(df_clean, cfg)
    regressions = predictive_regressions(rolling)
    safe_to_csv(rolling, cfg.outdir / "08_portfolio_rolling_metrics.csv")
    safe_to_csv(regressions, cfg.outdir / "09_predictive_regressions.csv")

    save_figures(df_clean, sec_stats, rolling, cfg.outdir)
    write_research_memo(cfg, overview, ranges, sec_stats, periods, ew_stats, rolling, regressions, cfg.outdir)

    print("\n[DONE] Outputs written to:", cfg.outdir.resolve())
    print("Next: send me research_memo.md, 04_security_stats.csv, 08_portfolio_rolling_metrics.csv and 09_predictive_regressions.csv")


if __name__ == "__main__":
    main()
