#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 2 robustness pipeline for MOEX DQ vs DR research.

Purpose
-------
This script is the second step after the exploratory screening. It is designed
to answer a narrower research question:

    Does DQ contain incremental predictive information about future tail risk
    beyond DR and current risk conditions?

Key improvements over the first script:
1) Fixed-period universes, not only full-sample coverage universes.
2) Separate robustness grids for windows, horizons and tail probabilities.
3) HAC/Newey-West standard errors for overlapping forward horizons.
4) Simple, nested model comparison: DQ alone, DR alone, DQ+DR, DQ+DR+controls.
5) VIF/correlation diagnostics for multicollinearity.
6) Lead/lag and placebo checks to detect regime/time-trend artifacts.
7) Tail-index-sorted portfolio groups for the article's original idea.

Required DB columns:
    secid, market, tradedate, log_return
Optional:
    boardid

Example:
python moex_dq_dr_stage2_robustness.py \
  --db-url postgresql://postgres:password2544@localhost:5432/heavy_tails_data \
  --table moex_total_return_daily \
  --outdir moex_stage2_outputs \
  --periods baseline_2018:2018-01-01:2026-05-15 shock_2022_2023:2022-01-01:2023-12-31 post_2024:2024-01-01:2026-05-15 \
  --windows 252 504 \
  --horizons 21 63 \
  --tail-probs 0.025 0.05 \
  --markets shares bonds

Author: ChatGPT research assistant
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from sqlalchemy import create_engine, inspect, text

try:
    import statsmodels.api as sm
except Exception:
    sm = None

try:
    from scipy.stats import spearmanr
except Exception:
    spearmanr = None


# ----------------------------
# Basic risk functions
# ----------------------------

def es_loss(losses: Sequence[float], tail_prob: float = 0.025) -> float:
    arr = np.asarray(losses, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan
    k = int(max(1, math.ceil(tail_prob * len(arr))))
    largest = np.partition(arr, len(arr) - k)[len(arr) - k:]
    return float(np.mean(largest))


def var_loss(losses: Sequence[float], tail_prob: float = 0.025) -> float:
    arr = np.asarray(losses, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan
    return float(np.quantile(arr, 1.0 - tail_prob))


def ann_vol(returns: Sequence[float]) -> float:
    arr = np.asarray(returns, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) < 2:
        return np.nan
    return float(np.std(arr, ddof=1) * np.sqrt(252.0))


def max_drawdown_log_returns(returns: Sequence[float]) -> float:
    arr = np.asarray(returns, dtype=float)
    arr = arr[np.isfinite(arr)]
    if len(arr) == 0:
        return np.nan
    wealth = np.exp(np.cumsum(arr))
    peak = np.maximum.accumulate(wealth)
    dd = wealth / peak - 1.0
    return float(-np.min(dd))


def hill_alpha(losses: Sequence[float], k: Optional[int] = None) -> float:
    x = np.asarray(losses, dtype=float)
    x = x[np.isfinite(x)]
    x = x[x > 0]
    n = len(x)
    if n < 50:
        return np.nan
    x = np.sort(x)
    if k is None:
        k = int(max(10, min(np.sqrt(n), 0.1 * n)))
    if k <= 1 or k >= n:
        return np.nan
    threshold = x[-k - 1]
    if threshold <= 0:
        return np.nan
    gamma = np.mean(np.log(x[-k:]) - np.log(threshold))
    if gamma <= 0 or not np.isfinite(gamma):
        return np.nan
    return float(1.0 / gamma)


def equal_weights(n: int) -> np.ndarray:
    return np.ones(n) / n


def dr_es(window: pd.DataFrame, weights: np.ndarray, tail_prob: float) -> float:
    x = window.dropna(how="any").to_numpy(dtype=float)
    if x.ndim != 2 or x.shape[0] < 60 or x.shape[1] != len(weights):
        return np.nan
    p = x @ weights
    p_es = es_loss(-p, tail_prob)
    indiv_es = np.array([es_loss(-x[:, j], tail_prob) for j in range(x.shape[1])])
    denom = float(np.dot(weights, indiv_es))
    if denom <= 0 or not np.isfinite(denom):
        return np.nan
    return float(p_es / denom)


def dq_es_empirical(
    window: pd.DataFrame,
    weights: np.ndarray,
    tail_prob: float,
    grid_size: int = 1000,
    max_tail_prob: float = 0.50,
) -> float:
    """
    Empirical inversion for ES-indexed DQ.

    This follows the working interpretation used in the first screening:
        beta* = inf { beta : ES_beta(portfolio) <= sum_i w_i ES_alpha(asset_i) }
        DQ = beta* / alpha

    This follows the Han-Lin-Wang DQ definition as a practical grid inversion.
    Han-Lin-Zhao (2025) studies empirical DQ estimators; this routine is a
    proxy implementation rather than a direct reproduction of their estimator.
    """
    x = window.dropna(how="any").to_numpy(dtype=float)
    if x.ndim != 2 or x.shape[0] < 60 or x.shape[1] != len(weights):
        return np.nan

    p = x @ weights
    indiv_es = np.array([es_loss(-x[:, j], tail_prob) for j in range(x.shape[1])])
    standalone = float(np.dot(weights, indiv_es))
    if standalone <= 0 or not np.isfinite(standalone):
        return np.nan

    n = len(p)
    min_prob = max(1.0 / n, 1e-4)
    max_prob = min(max(max_tail_prob, tail_prob * 1.25), 0.95)
    grid = np.linspace(min_prob, max_prob, grid_size)
    vals = np.array([es_loss(-p, b) for b in grid])

    # ES_beta decreases as beta increases under tail-probability parameterization.
    ok = np.where(vals <= standalone)[0]
    if len(ok) == 0:
        return np.nan
    idx = int(ok[0])

    # Linear interpolation around crossing to reduce grid artifacts.
    if idx == 0:
        beta_star = grid[0]
    else:
        x0, x1 = vals[idx - 1], vals[idx]
        b0, b1 = grid[idx - 1], grid[idx]
        if np.isfinite(x0) and np.isfinite(x1) and x0 != x1:
            # target = standalone, but vals descending
            beta_star = b0 + (standalone - x0) * (b1 - b0) / (x1 - x0)
            beta_star = float(np.clip(beta_star, b0, b1))
        else:
            beta_star = grid[idx]
    return float(beta_star / tail_prob)


# ----------------------------
# Data loading and preparation
# ----------------------------

def load_data(db_url: str, table: str, schema: Optional[str], start: Optional[str], end: Optional[str]) -> pd.DataFrame:
    engine = create_engine(db_url)
    insp = inspect(engine)
    cols_avail = [c["name"] for c in insp.get_columns(table, schema=schema)]
    need = ["secid", "market", "tradedate", "log_return"]
    missing = [c for c in need if c not in cols_avail]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    cols = need.copy()
    if "boardid" in cols_avail:
        cols.insert(2, "boardid")
    full = f"{schema}.{table}" if schema else table
    clauses = []
    params = {}
    if start:
        clauses.append("tradedate >= :start")
        params["start"] = start
    if end:
        clauses.append("tradedate <= :end")
        params["end"] = end
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    q = text(f"SELECT {', '.join(cols)} FROM {full} {where}")
    df = pd.read_sql(q, engine, params=params)
    df["tradedate"] = pd.to_datetime(df["tradedate"])
    df["secid"] = df["secid"].astype(str).str.strip()
    df["market"] = df["market"].astype(str).str.lower().str.strip()
    if "boardid" in df.columns:
        df["boardid"] = df["boardid"].astype(str).str.strip()
    df["log_return"] = pd.to_numeric(df["log_return"], errors="coerce")
    df = df[np.isfinite(df["log_return"])].copy()

    # Aggregate duplicate secid-market-date rows.
    df = (
        df.groupby(["market", "secid", "tradedate"], as_index=False)
        .agg(log_return=("log_return", "mean"))
        .sort_values(["market", "secid", "tradedate"])
    )
    return df


def parse_periods(raw_periods: List[str]) -> Dict[str, Tuple[str, str]]:
    out = {}
    for s in raw_periods:
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(f"Bad period specification {s}; expected name:YYYY-MM-DD:YYYY-MM-DD")
        out[parts[0]] = (parts[1], parts[2])
    return out


def select_universe(
    df: pd.DataFrame,
    market: str,
    start: str,
    end: str,
    min_coverage: float,
    max_assets: int,
    min_obs: int,
    max_zero_share: float,
    max_abs_return: float,
    prefer_prefixes: Optional[List[str]] = None,
) -> pd.DataFrame:
    d = df[(df["market"] == market) & (df["tradedate"] >= start) & (df["tradedate"] <= end)].copy()
    if d.empty:
        return pd.DataFrame()
    n_days = d["tradedate"].nunique()
    g = (
        d.groupby("secid")
        .agg(
            n_obs=("log_return", "size"),
            n_days=("tradedate", "nunique"),
            date_min=("tradedate", "min"),
            date_max=("tradedate", "max"),
            zero_share=("log_return", lambda x: float(np.mean(np.isclose(x, 0.0)))),
            abs_q99=("log_return", lambda x: float(np.nanquantile(np.abs(x), 0.99))),
            abs_max=("log_return", lambda x: float(np.nanmax(np.abs(x)))),
            ann_vol=("log_return", ann_vol),
            es_975=("log_return", lambda x: es_loss(-np.asarray(x), 0.025)),
            hill_alpha=("log_return", lambda x: hill_alpha(-np.asarray(x))),
        )
        .reset_index()
    )
    g["period_days"] = n_days
    g["coverage"] = g["n_days"] / n_days
    g["passes_basic"] = (
        (g["n_obs"] >= min_obs)
        & (g["coverage"] >= min_coverage)
        & (g["zero_share"] <= max_zero_share)
        & (g["abs_max"] <= max_abs_return)
    )

    if prefer_prefixes:
        pref = tuple(prefer_prefixes)
        g["prefix_preferred"] = g["secid"].str.startswith(pref)
    else:
        g["prefix_preferred"] = True

    candidates = g[g["passes_basic"] & g["prefix_preferred"]].copy()
    # Choose broad and relatively liquid-looking series: coverage first, then zero share, then observations.
    candidates = candidates.sort_values(["coverage", "zero_share", "n_obs"], ascending=[False, True, False])
    if max_assets > 0:
        candidates = candidates.head(max_assets)
    g["selected"] = g["secid"].isin(candidates["secid"])
    return g.sort_values(["selected", "coverage", "zero_share"], ascending=[False, False, True])


def pivot_returns(df: pd.DataFrame, secids: Sequence[str], market: str, start: str, end: str) -> pd.DataFrame:
    d = df[
        (df["market"] == market)
        & (df["secid"].isin(secids))
        & (df["tradedate"] >= start)
        & (df["tradedate"] <= end)
    ]
    p = d.pivot(index="tradedate", columns="secid", values="log_return").sort_index()
    return p


# ----------------------------
# Rolling metrics and portfolios
# ----------------------------

def rolling_metrics_for_pivot(
    pivot: pd.DataFrame,
    market: str,
    period_name: str,
    window: int,
    horizon: int,
    step: int,
    tail_prob: float,
    min_complete_ratio: float,
    min_assets: int,
    dq_grid_size: int,
) -> pd.DataFrame:
    records = []
    dates = pivot.index.to_list()
    n = len(dates)
    if n < window + horizon + 5:
        return pd.DataFrame()

    for end_ix in range(window, n - horizon, step):
        win = pivot.iloc[end_ix - window:end_ix]
        fut = pivot.iloc[end_ix:end_ix + horizon]
        # Drop assets not mostly present in this local window+future.
        local = pd.concat([win, fut], axis=0)
        valid_cols = local.columns[local.notna().mean(axis=0) >= min_complete_ratio]
        if len(valid_cols) < min_assets:
            continue
        win = win[valid_cols]
        fut = fut[valid_cols]
        # Use complete rows to avoid implicit cash/fill assumptions.
        win_cc = win.dropna(how="any")
        fut_cc = fut.dropna(how="any")
        if len(win_cc) < max(80, int(0.5 * window)) or len(fut_cc) < max(10, int(0.5 * horizon)):
            continue

        w = equal_weights(len(valid_cols))
        port_win = win_cc.to_numpy() @ w
        port_fut = fut_cc.to_numpy() @ w

        rec = {
            "market": market,
            "period": period_name,
            "tradedate": dates[end_ix],
            "window": window,
            "horizon": horizon,
            "tail_prob": tail_prob,
            "n_assets": len(valid_cols),
            "window_rows": len(win_cc),
            "future_rows": len(fut_cc),
            "dq_es": dq_es_empirical(win_cc, w, tail_prob, grid_size=dq_grid_size),
            "dr_es_concentration": dr_es(win_cc, w, tail_prob),
            "current_es": es_loss(-port_win, tail_prob),
            "current_var": var_loss(-port_win, tail_prob),
            "current_rv_ann": ann_vol(port_win),
            "current_hill_alpha": hill_alpha(-port_win),
            "future_es": es_loss(-port_fut, tail_prob),
            "future_var": var_loss(-port_fut, tail_prob),
            "future_rv_ann": ann_vol(port_fut),
            "future_mdd": max_drawdown_log_returns(port_fut),
            "future_cum_log_return": float(np.sum(port_fut)),
            "future_tail_event": int(np.any((-port_fut) > var_loss(-port_win, tail_prob))),
            "assets": ",".join(valid_cols),
        }
        records.append(rec)
    return pd.DataFrame(records)


def tail_group_portfolios(
    pivot: pd.DataFrame,
    market: str,
    period_name: str,
    window: int,
    horizon: int,
    step: int,
    tail_prob: float,
    min_complete_ratio: float,
    min_assets_per_group: int,
    n_groups: int,
) -> pd.DataFrame:
    records = []
    dates = pivot.index.to_list()
    n = len(dates)
    if n < window + horizon + 5:
        return pd.DataFrame()

    for end_ix in range(window, n - horizon, step):
        win = pivot.iloc[end_ix - window:end_ix]
        fut = pivot.iloc[end_ix:end_ix + horizon]
        local = pd.concat([win, fut], axis=0)
        valid = local.columns[local.notna().mean(axis=0) >= min_complete_ratio]
        if len(valid) < n_groups * min_assets_per_group:
            continue
        win = win[valid].dropna(how="any")
        fut = fut[valid].dropna(how="any")
        if len(win) < max(80, int(0.5 * window)) or len(fut) < max(10, int(0.5 * horizon)):
            continue

        alphas = pd.Series({c: hill_alpha(-win[c].to_numpy()) for c in valid})
        alphas = alphas.replace([np.inf, -np.inf], np.nan).dropna()
        if len(alphas) < n_groups * min_assets_per_group:
            continue
        # Lower alpha = heavier tail.
        ranks = alphas.rank(method="first", ascending=True)
        labels = pd.qcut(ranks, q=n_groups, labels=[f"tail_group_{i+1}" for i in range(n_groups)])

        for group_label in labels.cat.categories:
            cols = labels[labels == group_label].index.to_list()
            if len(cols) < min_assets_per_group:
                continue
            w = equal_weights(len(cols))
            pw = win[cols].to_numpy() @ w
            pf = fut[cols].to_numpy() @ w
            records.append({
                "market": market,
                "period": period_name,
                "tradedate": dates[end_ix],
                "window": window,
                "horizon": horizon,
                "tail_prob": tail_prob,
                "tail_group": group_label,
                "group_mean_alpha": float(alphas[cols].mean()),
                "n_assets": len(cols),
                "current_es": es_loss(-pw, tail_prob),
                "current_rv_ann": ann_vol(pw),
                "future_es": es_loss(-pf, tail_prob),
                "future_rv_ann": ann_vol(pf),
                "future_mdd": max_drawdown_log_returns(pf),
                "future_cum_log_return": float(np.sum(pf)),
                "assets": ",".join(cols),
            })
    return pd.DataFrame(records)


# ----------------------------
# Regression diagnostics
# ----------------------------

def add_regime_controls(d: pd.DataFrame) -> pd.DataFrame:
    x = d.copy()
    dt = pd.to_datetime(x["tradedate"])
    x["regime_covid"] = ((dt >= "2020-01-01") & (dt <= "2021-12-31")).astype(int)
    x["regime_2022_2023"] = ((dt >= "2022-01-01") & (dt <= "2023-12-31")).astype(int)
    x["regime_post_2024"] = (dt >= "2024-01-01").astype(int)
    x["near_2022_trade_break"] = ((dt >= "2022-02-01") & (dt <= "2022-05-31")).astype(int)
    return x


def vif_table(d: pd.DataFrame, cols: List[str], group_keys: Dict[str, object]) -> pd.DataFrame:
    if sm is None:
        return pd.DataFrame()
    rows = []
    for col in cols:
        others = [c for c in cols if c != col]
        dd = d[[col] + others].replace([np.inf, -np.inf], np.nan).dropna()
        if len(dd) < len(cols) + 5:
            continue
        try:
            m = sm.OLS(dd[col], sm.add_constant(dd[others])).fit()
            r2 = float(m.rsquared)
            vif = np.inf if r2 >= 0.999999 else 1.0 / (1.0 - r2)
        except Exception:
            r2, vif = np.nan, np.nan
        rows.append({**group_keys, "variable": col, "aux_r2": r2, "vif": vif})
    return pd.DataFrame(rows)


def run_ols_hac(d: pd.DataFrame, y: str, xcols: List[str], group_keys: Dict[str, object], hac_lags: int) -> pd.DataFrame:
    if sm is None:
        return pd.DataFrame()
    dd = d[[y] + xcols].replace([np.inf, -np.inf], np.nan).dropna()
    if len(dd) < max(30, len(xcols) + 10):
        return pd.DataFrame()
    X = sm.add_constant(dd[xcols], has_constant="add")
    model = sm.OLS(dd[y], X).fit(cov_type="HAC", cov_kwds={"maxlags": max(1, int(hac_lags))})
    rows = []
    for p in model.params.index:
        rows.append({
            **group_keys,
            "dependent": y,
            "spec": "+".join(xcols),
            "n_obs": int(model.nobs),
            "r2": float(model.rsquared),
            "adj_r2": float(model.rsquared_adj),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "param": p,
            "coef": float(model.params[p]),
            "std_err_hac": float(model.bse[p]),
            "t_hac": float(model.tvalues[p]),
            "pvalue_hac": float(model.pvalues[p]),
        })
    return pd.DataFrame(rows)


def regression_suite(roll: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if roll.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    d = add_regime_controls(roll)
    depvars = ["future_es", "future_var", "future_rv_ann", "future_mdd", "future_tail_event"]
    specs = {
        "dq_only": ["dq_es"],
        "dr_only": ["dr_es_concentration"],
        "dq_dr": ["dq_es", "dr_es_concentration"],
        "dq_dr_current_es": ["dq_es", "dr_es_concentration", "current_es"],
        "risk_controls": ["current_es", "current_rv_ann", "current_hill_alpha", "n_assets"],
        "full": [
            "dq_es", "dr_es_concentration", "current_es", "current_rv_ann",
            "current_hill_alpha", "n_assets", "regime_covid",
            "regime_2022_2023", "regime_post_2024", "near_2022_trade_break"
        ],
    }

    reg_rows = []
    corr_rows = []
    vif_rows = []
    placebo_rows = []

    group_cols = ["market", "period", "window", "horizon", "tail_prob"]
    for key, g in d.groupby(group_cols, dropna=False):
        keys = dict(zip(group_cols, key))
        hac_lags = max(1, int(math.ceil(float(keys["horizon"]) / 21.0)) + 1)

        # correlations
        corr_vars = ["dq_es", "dr_es_concentration", "current_es", "current_rv_ann", "current_hill_alpha", "n_assets"] + depvars
        for a, b in itertools.combinations(corr_vars, 2):
            gg = g[[a, b]].replace([np.inf, -np.inf], np.nan).dropna()
            if len(gg) < 10:
                continue
            pearson = float(gg[a].corr(gg[b]))
            if spearmanr is not None:
                sp = spearmanr(gg[a], gg[b], nan_policy="omit")
                spear, spear_p = float(sp.statistic), float(sp.pvalue)
            else:
                spear, spear_p = np.nan, np.nan
            corr_rows.append({**keys, "x": a, "y": b, "n": len(gg), "pearson": pearson, "spearman": spear, "spearman_p": spear_p})

        vif_rows.append(vif_table(g, ["dq_es", "dr_es_concentration", "current_es", "current_rv_ann", "current_hill_alpha", "n_assets"], keys))

        for y in depvars:
            for spec_name, xcols in specs.items():
                out = run_ols_hac(g, y, xcols, {**keys, "spec_name": spec_name}, hac_lags=hac_lags)
                if not out.empty:
                    reg_rows.append(out)

        # placebo: shuffle dq/dr within group and rerun dq_dr model 200 times, store distribution of t-stats.
        rng = np.random.default_rng(42)
        base = g.copy().reset_index(drop=True)
        for y in ["future_es", "future_mdd"]:
            dd = base[[y, "dq_es", "dr_es_concentration"]].dropna()
            if len(dd) < 50:
                continue
            t_dq = []
            t_dr = []
            for _ in range(200):
                pp = dd.copy()
                pp["dq_es"] = rng.permutation(pp["dq_es"].to_numpy())
                pp["dr_es_concentration"] = rng.permutation(pp["dr_es_concentration"].to_numpy())
                out = run_ols_hac(pp, y, ["dq_es", "dr_es_concentration"], keys, hac_lags)
                if out.empty:
                    continue
                dq_row = out[out["param"] == "dq_es"]
                dr_row = out[out["param"] == "dr_es_concentration"]
                if not dq_row.empty:
                    t_dq.append(float(dq_row["t_hac"].iloc[0]))
                if not dr_row.empty:
                    t_dr.append(float(dr_row["t_hac"].iloc[0]))
            placebo_rows.append({
                **keys,
                "dependent": y,
                "n_placebo": len(t_dq),
                "placebo_abs_t_dq_q95": float(np.nanquantile(np.abs(t_dq), 0.95)) if t_dq else np.nan,
                "placebo_abs_t_dr_q95": float(np.nanquantile(np.abs(t_dr), 0.95)) if t_dr else np.nan,
            })

    regs = pd.concat(reg_rows, ignore_index=True) if reg_rows else pd.DataFrame()
    corrs = pd.DataFrame(corr_rows)
    vifs = pd.concat(vif_rows, ignore_index=True) if vif_rows else pd.DataFrame()
    placebo = pd.DataFrame(placebo_rows)
    return regs, corrs, vifs, placebo


def tail_group_tests(groups: pd.DataFrame) -> pd.DataFrame:
    if groups.empty or sm is None:
        return pd.DataFrame()
    rows = []
    depvars = ["future_es", "future_rv_ann", "future_mdd"]
    group_cols = ["market", "period", "window", "horizon", "tail_prob"]
    for key, g in groups.groupby(group_cols, dropna=False):
        keys = dict(zip(group_cols, key))
        # Encode group labels as ordered severity: group_1 = heaviest tails
        dd = g.copy()
        dd["tail_rank"] = dd["tail_group"].str.extract(r"(\d+)").astype(float)
        for y in depvars:
            out = run_ols_hac(dd, y, ["tail_rank", "current_es", "current_rv_ann"], keys, hac_lags=max(1, int(math.ceil(keys["horizon"] / 21.0)) + 1))
            if not out.empty:
                rows.append(out)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()



def _stage2_combo_worker(task: tuple) -> tuple:
    """Worker for one (window, horizon, tail_prob) combination within one period-market pivot."""
    (
        pivot,
        market,
        period_name,
        window,
        horizon,
        step,
        tail_prob,
        min_complete_ratio,
        min_assets_window,
        dq_grid_size,
        min_assets_tail_group,
        n_tail_groups,
    ) = task
    rm = rolling_metrics_for_pivot(
        pivot,
        market,
        period_name,
        int(window),
        int(horizon),
        int(step),
        float(tail_prob),
        float(min_complete_ratio),
        int(min_assets_window),
        int(dq_grid_size),
    )
    tg = tail_group_portfolios(
        pivot,
        market,
        period_name,
        int(window),
        int(horizon),
        int(step),
        float(tail_prob),
        float(min_complete_ratio),
        int(min_assets_tail_group),
        int(n_tail_groups),
    )
    return rm, tg

def save(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[WRITE] {path} rows={len(df):,}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-url", default="postgresql://postgres:password2544@localhost:5432/heavy_tails_data")
    ap.add_argument("--table", default="moex_total_return_daily")
    ap.add_argument("--schema", default=None)
    ap.add_argument("--outdir", default="moex_stage2_outputs")
    ap.add_argument("--periods", nargs="+", default=[
        "full_2015:2015-01-01:2026-05-15",
        "baseline_2018:2018-01-01:2026-05-15",
        "covid_2020_2021:2020-01-01:2021-12-31",
        "shock_2022_2023:2022-01-01:2023-12-31",
        "post_2024:2024-01-01:2026-05-15",
    ])
    ap.add_argument("--markets", nargs="+", default=["shares", "bonds"])
    ap.add_argument("--windows", nargs="+", type=int, default=[252, 504])
    ap.add_argument("--horizons", nargs="+", type=int, default=[21, 63])
    ap.add_argument("--tail-probs", nargs="+", type=float, default=[0.025, 0.05])
    ap.add_argument("--step", type=int, default=21)
    ap.add_argument("--min-coverage", type=float, default=0.90)
    ap.add_argument("--min-obs", type=int, default=500)
    ap.add_argument("--min-complete-ratio", type=float, default=0.80)
    ap.add_argument("--min-assets-window", type=int, default=10)
    ap.add_argument("--max-assets-shares", type=int, default=80)
    ap.add_argument("--max-assets-bonds", type=int, default=120)
    ap.add_argument("--max-zero-share-shares", type=float, default=0.25)
    ap.add_argument("--max-zero-share-bonds", type=float, default=0.50)
    ap.add_argument("--max-abs-return", type=float, default=1.0)
    ap.add_argument("--dq-grid-size", type=int, default=1000)
    ap.add_argument("--n-tail-groups", type=int, default=3)
    ap.add_argument("--min-assets-tail-group", type=int, default=8)
    ap.add_argument("--n-jobs", type=int, default=1, help="Parallel workers for window/horizon/tail-prob grid within each market-period. Use 1 for serial.")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / "00_stage2_config.json").open("w", encoding="utf-8") as f:
        json.dump(vars(args), f, ensure_ascii=False, indent=2)

    periods = parse_periods(args.periods)
    global_start = min(s for s, e in periods.values())
    global_end = max(e for s, e in periods.values())
    df = load_data(args.db_url, args.table, args.schema, global_start, global_end)

    all_universes = []
    all_roll = []
    all_groups = []

    for period_name, (start, end) in periods.items():
        for market in args.markets:
            max_assets = args.max_assets_shares if market == "shares" else args.max_assets_bonds
            max_zero = args.max_zero_share_shares if market == "shares" else args.max_zero_share_bonds
            # Do not force bond prefix by default; if needed, filter SU for OFZ in a separate run.
            uni = select_universe(
                df, market, start, end,
                min_coverage=args.min_coverage,
                max_assets=max_assets,
                min_obs=args.min_obs,
                max_zero_share=max_zero,
                max_abs_return=args.max_abs_return,
                prefer_prefixes=None,
            )
            if uni.empty:
                continue
            uni["period"] = period_name
            all_universes.append(uni.assign(market=market))
            selected = uni[uni["selected"]]["secid"].tolist()
            print(f"[UNIVERSE] {period_name}/{market}: selected {len(selected)}")
            if len(selected) < args.min_assets_window:
                continue
            pivot = pivot_returns(df, selected, market, start, end)
            combos = list(itertools.product(args.windows, args.horizons, args.tail_probs))
            tasks = [
                (
                    pivot,
                    market,
                    period_name,
                    window,
                    horizon,
                    args.step,
                    tail_prob,
                    args.min_complete_ratio,
                    args.min_assets_window,
                    args.dq_grid_size,
                    args.min_assets_tail_group,
                    args.n_tail_groups,
                )
                for window, horizon, tail_prob in combos
            ]
            workers = max(1, int(args.n_jobs))
            if workers == 1 or len(tasks) <= 1:
                for task in tasks:
                    rm, tg = _stage2_combo_worker(task)
                    if not rm.empty:
                        all_roll.append(rm)
                    if not tg.empty:
                        all_groups.append(tg)
            else:
                workers = min(workers, len(tasks))
                print(f"[PARALLEL] {period_name}/{market}: {len(tasks)} grid jobs with n_jobs={workers}")
                with ProcessPoolExecutor(max_workers=workers) as ex:
                    futures = [ex.submit(_stage2_combo_worker, task) for task in tasks]
                    for fut in as_completed(futures):
                        rm, tg = fut.result()
                        if not rm.empty:
                            all_roll.append(rm)
                        if not tg.empty:
                            all_groups.append(tg)

    universes = pd.concat(all_universes, ignore_index=True) if all_universes else pd.DataFrame()
    roll = pd.concat(all_roll, ignore_index=True) if all_roll else pd.DataFrame()
    groups = pd.concat(all_groups, ignore_index=True) if all_groups else pd.DataFrame()

    save(universes, outdir / "01_stage2_universes.csv")
    save(roll, outdir / "02_stage2_rolling_metrics.csv")
    save(groups, outdir / "03_tail_group_portfolios.csv")

    regs, corrs, vifs, placebo = regression_suite(roll)
    save(regs, outdir / "04_stage2_regressions_hac.csv")
    save(corrs, outdir / "05_stage2_correlations.csv")
    save(vifs, outdir / "06_stage2_vif.csv")
    save(placebo, outdir / "07_stage2_placebo.csv")

    tail_tests = tail_group_tests(groups)
    save(tail_tests, outdir / "08_tail_group_tests.csv")

    # Compact summary for quick reading.
    summary_rows = []
    if not regs.empty:
        focus = regs[regs["param"].isin(["dq_es", "dr_es_concentration"])]
        for _, r in focus.iterrows():
            summary_rows.append({
                "market": r["market"],
                "period": r["period"],
                "window": r["window"],
                "horizon": r["horizon"],
                "tail_prob": r["tail_prob"],
                "dependent": r["dependent"],
                "spec_name": r["spec_name"],
                "param": r["param"],
                "coef": r["coef"],
                "t_hac": r["t_hac"],
                "pvalue_hac": r["pvalue_hac"],
                "r2": r["r2"],
                "n_obs": r["n_obs"],
            })
    summary = pd.DataFrame(summary_rows)
    save(summary, outdir / "09_focus_summary_dq_dr.csv")

    with (outdir / "research_stage2_memo.md").open("w", encoding="utf-8") as f:
        f.write("# Stage 2 robustness memo\n\n")
        f.write("## Outputs\n")
        f.write("- `01_stage2_universes.csv`: selected universes by market and period.\n")
        f.write("- `02_stage2_rolling_metrics.csv`: rolling DQ/DR and future risk metrics.\n")
        f.write("- `04_stage2_regressions_hac.csv`: nested HAC regressions.\n")
        f.write("- `06_stage2_vif.csv`: multicollinearity diagnostics.\n")
        f.write("- `08_tail_group_tests.csv`: test of tail-index-sorted portfolio groups.\n")
        f.write("- `09_focus_summary_dq_dr.csv`: compact DQ/DR coefficient table.\n\n")
        if not roll.empty:
            f.write("## Rolling observations by market/period\n\n")
            f.write(roll.groupby(["market", "period", "window", "horizon", "tail_prob"]).size().rename("n").reset_index().to_markdown(index=False))
            f.write("\n\n")
        if not summary.empty:
            f.write("## Significant DQ/DR coefficients at 10% level\n\n")
            sig = summary[summary["pvalue_hac"] < 0.10].copy()
            if sig.empty:
                f.write("No DQ/DR coefficients significant at 10% in the focus table.\n")
            else:
                f.write(sig.to_markdown(index=False))
                f.write("\n")
    print(f"[WRITE] {outdir / 'research_stage2_memo.md'}")


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    main()
