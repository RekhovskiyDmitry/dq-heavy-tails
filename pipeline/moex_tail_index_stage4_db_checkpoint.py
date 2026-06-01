#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 4: Robust tail-index estimation for MOEX DQ vs DR research.

Purpose
-------
This script builds an article-ready tail-index layer for a MOEX panel of
adjusted daily log returns. It is designed to test the working hypothesis:

    * DR should work well when tail-index alpha > 2;
    * DR may be structurally weak relative to DQ when alpha < 1.

The second point is a hypothesis, not a conclusion. Current article results do
not find a defensible strict alpha < 1 regime in liquid MOEX equities.

The script estimates lower-tail alpha for each security on rolling windows,
uses several EVT estimators, chooses an adaptive threshold k, quantifies
uncertainty by block bootstrap, and assigns strict / uncertain tail groups.

Expected input columns
----------------------
Required:
    secid, market, tradedate, log_return
Optional but recommended:
    boardid, cashflow, adjusted_close

Default DB example:
    postgresql://postgres:password2544@localhost:5432/heavy_tails_data

Example usage
-------------
Fast pilot on shares only:

python moex_tail_index_stage4.py \
  --db-url postgresql://postgres:password2544@localhost:5432/heavy_tails_data \
  --table moex_daily_returns \
  --outdir moex_tail_stage4_pilot \
  --markets shares \
  --start-date 2018-01-01 \
  --windows 504 \
  --step 21 \
  --bootstrap-reps 100 \
  --n-jobs 4

Main run, lower-tail, raw returns:

python moex_tail_index_stage4.py \
  --db-url postgresql://postgres:password2544@localhost:5432/heavy_tails_data \
  --table moex_daily_returns \
  --outdir moex_tail_stage4_full \
  --markets shares bonds \
  --start-date 2018-01-01 \
  --windows 252 504 \
  --step 21 \
  --bootstrap-reps 500 \
  --n-jobs 8

Filtered residual robustness using EWMA volatility standardization:

python moex_tail_index_stage4.py \
  --db-url postgresql://postgres:password2544@localhost:5432/heavy_tails_data \
  --table moex_daily_returns \
  --outdir moex_tail_stage4_filtered \
  --markets shares bonds \
  --start-date 2018-01-01 \
  --windows 504 \
  --step 21 \
  --filter-method ewma \
  --bootstrap-reps 500 \
  --n-jobs 8

Outputs
-------
00_tail_config.json
01_data_audit.csv
02_universe_summary.csv
03_tail_alpha_estimates.csv / parquet if pyarrow is installed
04_tail_group_counts.csv
05_estimator_summary.csv
06_group_membership_latest.csv
07_diagnostic_candidates.csv
figures/*.png

Notes
-----
- The primary tail side is lower tail: X_t = -r_t, positive losses only.
- The main consensus alpha is median(Hill, MOM, GPD-MLE) at selected k.
- Strict alpha<1 and alpha>2 labels are assigned conservatively using
  bootstrap probabilities and confidence intervals.
- This is not a trading script and does not optimize portfolios.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import warnings
from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import OptimizeWarning
from sqlalchemy import bindparam, create_engine, inspect, text
from tqdm import tqdm

warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=OptimizeWarning)


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

@dataclass
class TailConfig:
    db_url: str
    table: str
    outdir: str
    markets: List[str]
    start_date: Optional[str]
    end_date: Optional[str]
    windows: List[int]
    step: int
    tail_side: str
    filter_method: str
    ewma_span: int
    core_universe: bool
    min_obs_core: int
    min_obs_broad: int
    coverage_core_shares: float
    coverage_core_bonds: float
    coverage_broad_shares: float
    coverage_broad_bonds: float
    zero_share_core_shares: float
    zero_share_core_bonds: float
    zero_share_broad_shares: float
    zero_share_broad_bonds: float
    zero_tol: float
    min_tail_obs: int
    min_k: int
    k_min_frac: float
    k_max_frac: float
    adaptive_grid_step: int
    bootstrap_reps: int
    block_lengths: List[int]
    bootstrap_reselect_k: bool
    ci_level: float
    strict_prob: float
    theta_run_length: int
    theta_declustering_cutoff: float
    max_securities_per_market: Optional[int]
    random_seed: int
    n_jobs: int
    max_abs_return_for_audit: float
    db_write_intermediate: bool
    db_results_table: str
    db_progress_table: str
    db_chunksize: int
    run_id: str


# -----------------------------------------------------------------------------
# I/O helpers
# -----------------------------------------------------------------------------

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_table(df: pd.DataFrame, path_stem: str) -> str:
    """Save as parquet if available, otherwise CSV. Always also save CSV for small tables."""
    if df.empty:
        csv_path = f"{path_stem}.csv"
        df.to_csv(csv_path, index=False)
        return csv_path
    try:
        parquet_path = f"{path_stem}.parquet"
        df.to_parquet(parquet_path, index=False)
        csv_path = f"{path_stem}.csv"
        # CSV is useful for quick inspection; for very large files still create it
        # because the research workflow has been CSV-based so far.
        df.to_csv(csv_path, index=False)
        return parquet_path
    except Exception:
        csv_path = f"{path_stem}.csv"
        df.to_csv(csv_path, index=False)
        return csv_path



_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def split_db_table_name(table_name: str) -> Tuple[Optional[str], str]:
    """Split optional schema-qualified table name into (schema, table)."""
    parts = table_name.split(".")
    if len(parts) == 1:
        schema, name = None, parts[0]
    elif len(parts) == 2:
        schema, name = parts
    else:
        raise ValueError(f"Invalid table name: {table_name!r}. Use table or schema.table")
    for part in [p for p in [schema, name] if p is not None]:
        if not _IDENTIFIER_RE.match(part):
            raise ValueError(
                f"Unsafe table/schema identifier {part!r}. Use letters, digits and underscore only."
            )
    return schema, name


def qualified_db_table_name(table_name: str) -> str:
    """Return a safely quoted table name for raw SQL statements."""
    schema, name = split_db_table_name(table_name)
    if schema:
        return f'"{schema}"."{name}"'
    return f'"{name}"'


def init_intermediate_db_tables(cfg: TailConfig) -> None:
    """Create the progress table used for per-security checkpoints."""
    engine = create_engine(cfg.db_url)
    progress_table = qualified_db_table_name(cfg.db_progress_table)
    with engine.begin() as con:
        con.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS {progress_table} (
                    run_id TEXT NOT NULL,
                    market TEXT NOT NULL,
                    secid TEXT NOT NULL,
                    status TEXT NOT NULL,
                    n_estimates INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    finished_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    PRIMARY KEY (run_id, market, secid)
                )
                """
            )
        )


def write_security_checkpoint_to_db(
    cfg: TailConfig,
    security_rows: List[Dict[str, object]],
    market: str,
    secid: str,
    status: str = "done",
    error: Optional[str] = None,
) -> None:
    """Persist all rolling estimates for one security after that security finishes.

    The parent process calls this after fut.result(), so worker processes do not
    write to PostgreSQL concurrently. For the same run_id/market/secid, existing
    rows are deleted before append, which makes reruns with the same run_id safe.
    """
    engine = create_engine(cfg.db_url)
    results_schema, results_name = split_db_table_name(cfg.db_results_table)
    progress_table = qualified_db_table_name(cfg.db_progress_table)
    results_table_sql = qualified_db_table_name(cfg.db_results_table)

    if security_rows:
        df = pd.DataFrame(security_rows).copy()
        df.insert(0, "run_id", cfg.run_id)
        df["written_at"] = pd.Timestamp.now(tz="UTC")
        if "window_start" in df.columns:
            df["window_start"] = pd.to_datetime(df["window_start"])
        if "window_end" in df.columns:
            df["window_end"] = pd.to_datetime(df["window_end"])

        # If this security was already checkpointed for this run_id, replace it.
        inspector = inspect(engine)
        if inspector.has_table(results_name, schema=results_schema):
            with engine.begin() as con:
                con.execute(
                    text(
                        f"""
                        DELETE FROM {results_table_sql}
                        WHERE run_id = :run_id AND market = :market AND secid = :secid
                        """
                    ),
                    {"run_id": cfg.run_id, "market": market, "secid": secid},
                )

        df.to_sql(
            results_name,
            engine,
            schema=results_schema,
            if_exists="append",
            index=False,
            chunksize=cfg.db_chunksize,
            method="multi",
        )

    with engine.begin() as con:
        con.execute(
            text(
                f"""
                INSERT INTO {progress_table}
                    (run_id, market, secid, status, n_estimates, error, finished_at)
                VALUES
                    (:run_id, :market, :secid, :status, :n_estimates, :error, now())
                ON CONFLICT (run_id, market, secid)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    n_estimates = EXCLUDED.n_estimates,
                    error = EXCLUDED.error,
                    finished_at = EXCLUDED.finished_at
                """
            ),
            {
                "run_id": cfg.run_id,
                "market": market,
                "secid": secid,
                "status": status,
                "n_estimates": len(security_rows),
                "error": error[:4000] if error else None,
            },
        )


def finite_or_nan(x: object) -> float:
    try:
        y = float(x)
        if np.isfinite(y):
            return y
        return np.nan
    except Exception:
        return np.nan


# -----------------------------------------------------------------------------
# Data loading and preprocessing
# -----------------------------------------------------------------------------

def load_returns(cfg: TailConfig) -> pd.DataFrame:
    engine = create_engine(cfg.db_url)

    # Introspect columns to avoid failing when optional fields are absent.
    with engine.connect() as con:
        cols = pd.read_sql(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table
                """
            ),
            con,
            params={"table": cfg.table.split(".")[-1]},
        )["column_name"].str.lower().tolist()

    required = ["secid", "market", "tradedate", "log_return"]
    missing = [c for c in required if c not in cols]
    if missing:
        raise ValueError(f"Table {cfg.table} is missing required columns: {missing}")

    optional = [c for c in ["boardid", "cashflow", "adjusted_close"] if c in cols]
    select_cols = required + optional
    sql = f"SELECT {', '.join(select_cols)} FROM {cfg.table}"

    filters = []
    if cfg.start_date:
        filters.append("tradedate >= :start_date")
    if cfg.end_date:
        filters.append("tradedate <= :end_date")
    if cfg.markets:
        filters.append("market IN :markets")
    if filters:
        sql += " WHERE " + " AND ".join(filters)

    params = {
        "start_date": cfg.start_date,
        "end_date": cfg.end_date,
        "markets": cfg.markets,
    }
    sql_obj = text(sql)
    if cfg.markets:
        sql_obj = sql_obj.bindparams(bindparam("markets", expanding=True))
    df = pd.read_sql(sql_obj, engine, params=params)
    df.columns = [c.lower() for c in df.columns]
    if "boardid" not in df.columns:
        df["boardid"] = "UNKNOWN"
    df["tradedate"] = pd.to_datetime(df["tradedate"])
    df["log_return"] = pd.to_numeric(df["log_return"], errors="coerce")
    df["secid"] = df["secid"].astype(str)
    df["market"] = df["market"].astype(str).str.lower()
    df["boardid"] = df["boardid"].fillna("UNKNOWN").astype(str)
    return df


def choose_canonical_boards(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Choose one board per secid-market pair. Do not average across boards."""
    priority = {
        "shares": ["TQBR"],
        "bonds": ["TQCB", "TQOB", "TQOD", "TQOY"],
    }

    rows = []
    for (secid, market), g in df.groupby(["secid", "market"], sort=False):
        counts = g.groupby("boardid").size().sort_values(ascending=False)
        available = list(counts.index)
        chosen = None
        for b in priority.get(market, []):
            if b in available:
                chosen = b
                break
        if chosen is None:
            chosen = str(counts.index[0])
        rows.append(
            {
                "secid": secid,
                "market": market,
                "chosen_boardid": chosen,
                "n_boards": len(available),
                "all_boards": ";".join(map(str, available)),
                "chosen_board_nobs": int(counts.loc[chosen]),
                "max_board_nobs": int(counts.iloc[0]),
            }
        )

    board_map = pd.DataFrame(rows)
    out = df.merge(board_map[["secid", "market", "chosen_boardid"]], on=["secid", "market"], how="left")
    out = out[out["boardid"].astype(str) == out["chosen_boardid"].astype(str)].copy()
    out = out.drop(columns=["chosen_boardid"])
    return out, board_map


def apply_filter_method(df: pd.DataFrame, cfg: TailConfig) -> pd.DataFrame:
    """Add model_return column: raw log_return or simple EWMA-vol filtered residual."""
    df = df.sort_values(["market", "secid", "tradedate"]).copy()
    if cfg.filter_method == "raw":
        df["model_return"] = df["log_return"]
        return df

    if cfg.filter_method == "ewma":
        # A robust, dependency-light de-volatilization. This is not a full GARCH fit,
        # but it gives a useful filtered-tail robustness layer at panel scale.
        def _ewma_standardize(s: pd.Series) -> pd.Series:
            sigma = s.ewm(span=cfg.ewma_span, adjust=False, min_periods=max(20, cfg.ewma_span // 2)).std()
            sigma = sigma.shift(1)
            med = sigma.replace([np.inf, -np.inf], np.nan).median()
            sigma = sigma.fillna(med)
            sigma = sigma.replace(0.0, np.nan).fillna(med if med and med > 0 else 1.0)
            return s / sigma

        df["model_return"] = df.groupby(["market", "secid"], group_keys=False)["log_return"].apply(_ewma_standardize)
        df["model_return"] = df["model_return"].replace([np.inf, -np.inf], np.nan)
        return df

    raise ValueError(f"Unknown filter method: {cfg.filter_method}")


def make_data_audit(raw: pd.DataFrame, canonical: pd.DataFrame, board_map: pd.DataFrame, cfg: TailConfig) -> pd.DataFrame:
    rows = []
    rows.append({"item": "raw_rows", "value": len(raw)})
    rows.append({"item": "canonical_board_rows", "value": len(canonical)})
    rows.append({"item": "n_securities_raw", "value": raw[["secid", "market"]].drop_duplicates().shape[0]})
    rows.append({"item": "n_securities_canonical", "value": canonical[["secid", "market"]].drop_duplicates().shape[0]})
    rows.append({"item": "missing_log_return_raw", "value": int(raw["log_return"].isna().sum())})
    rows.append({"item": "nonfinite_model_return", "value": int(canonical["model_return"].replace([np.inf, -np.inf], np.nan).isna().sum())})
    rows.append({"item": "multi_board_securities", "value": int((board_map["n_boards"] > 1).sum())})
    rows.append({"item": "audit_abs_return_gt_threshold", "value": int((raw["log_return"].abs() > cfg.max_abs_return_for_audit).sum())})
    return pd.DataFrame(rows)


def build_universe(df: pd.DataFrame, cfg: TailConfig) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Compute coverage/zero-share and select core/broad securities."""
    trading_days = df.groupby("market")["tradedate"].nunique().to_dict()
    rows = []
    for (market, secid), g in df.groupby(["market", "secid"], sort=False):
        n = int(g["model_return"].replace([np.inf, -np.inf], np.nan).notna().sum())
        expected = int(trading_days.get(market, np.nan))
        coverage = n / expected if expected > 0 else np.nan
        zero_share = float((g["model_return"].fillna(np.nan).abs() <= cfg.zero_tol).sum() / max(n, 1))
        rows.append(
            {
                "market": market,
                "secid": secid,
                "n_obs": n,
                "expected_market_days": expected,
                "coverage": coverage,
                "zero_share": zero_share,
                "first_date": g["tradedate"].min(),
                "last_date": g["tradedate"].max(),
                "mean_return": g["model_return"].mean(),
                "std_return": g["model_return"].std(),
                "max_abs_return": g["model_return"].abs().max(),
            }
        )
    uni = pd.DataFrame(rows)

    def flags(row: pd.Series) -> Tuple[bool, bool]:
        market = row["market"]
        if market == "shares":
            c_core, c_broad = cfg.coverage_core_shares, cfg.coverage_broad_shares
            z_core, z_broad = cfg.zero_share_core_shares, cfg.zero_share_broad_shares
        else:
            c_core, c_broad = cfg.coverage_core_bonds, cfg.coverage_broad_bonds
            z_core, z_broad = cfg.zero_share_core_bonds, cfg.zero_share_broad_bonds
        core = (row["n_obs"] >= cfg.min_obs_core) and (row["coverage"] >= c_core) and (row["zero_share"] <= z_core)
        broad = (row["n_obs"] >= cfg.min_obs_broad) and (row["coverage"] >= c_broad) and (row["zero_share"] <= z_broad)
        return core, broad

    fl = uni.apply(flags, axis=1, result_type="expand")
    uni["core_liquid"] = fl[0]
    uni["broad"] = fl[1]

    use_col = "core_liquid" if cfg.core_universe else "broad"
    selected = uni[uni[use_col]].copy()

    if cfg.max_securities_per_market is not None:
        parts = []
        for m, g in selected.groupby("market"):
            parts.append(g.sort_values(["coverage", "n_obs"], ascending=False).head(cfg.max_securities_per_market))
        selected = pd.concat(parts, ignore_index=True) if parts else selected

    return uni, selected


# -----------------------------------------------------------------------------
# Tail transformations and estimators
# -----------------------------------------------------------------------------

def transform_tail(r: np.ndarray, side: str, positive_only: bool = True) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    r = r[np.isfinite(r)]
    if side == "lower":
        x = -r
    elif side == "upper":
        x = r
    elif side == "abs":
        x = np.abs(r)
    else:
        raise ValueError(f"Unknown tail side: {side}")
    x = x[np.isfinite(x)]
    if positive_only:
        x = x[x > 0]
    return x


def sorted_desc_positive(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x) & (x > 0)]
    if x.size == 0:
        return x
    return np.sort(x)[::-1]


def hill_alpha(x: np.ndarray, k: int) -> float:
    y = sorted_desc_positive(x)
    if k < 2 or y.size <= k:
        return np.nan
    threshold = y[k]
    if threshold <= 0:
        return np.nan
    logs = np.log(y[:k]) - math.log(threshold)
    gamma = float(np.mean(logs))
    if not np.isfinite(gamma) or gamma <= 0:
        return np.nan
    return 1.0 / gamma


def mom_alpha(x: np.ndarray, k: int) -> float:
    """Dekkers-Einmahl-de Haan moment estimator. Returns alpha=1/gamma."""
    y = sorted_desc_positive(x)
    if k < 3 or y.size <= k:
        return np.nan
    threshold = y[k]
    if threshold <= 0:
        return np.nan
    z = np.log(y[:k]) - math.log(threshold)
    m1 = float(np.mean(z))
    m2 = float(np.mean(z ** 2))
    if not np.isfinite(m1) or not np.isfinite(m2) or m1 <= 0 or m2 <= 0:
        return np.nan
    denom = 1.0 - (m1 * m1 / m2)
    if not np.isfinite(denom) or abs(denom) < 1e-12:
        return np.nan
    gamma = m1 + 1.0 - 0.5 / denom
    if not np.isfinite(gamma) or gamma <= 0:
        return np.nan
    return 1.0 / gamma


def pickands_alpha(x: np.ndarray, k: int) -> float:
    y_asc = np.sort(np.asarray(x, dtype=float)[np.isfinite(x) & (np.asarray(x, dtype=float) > 0)])
    n = y_asc.size
    if k < 1 or 4 * k >= n:
        return np.nan
    # Extreme order statistics in ascending order.
    x1 = y_asc[n - k]
    x2 = y_asc[n - 2 * k]
    x4 = y_asc[n - 4 * k]
    num = x1 - x2
    den = x2 - x4
    if num <= 0 or den <= 0:
        return np.nan
    gamma = math.log(num / den) / math.log(2.0)
    if not np.isfinite(gamma) or gamma <= 0:
        return np.nan
    return 1.0 / gamma


def trimmed_hill_alpha(x: np.ndarray, k: int, trim_frac: float = 0.05) -> float:
    """Simple diagnostic top-trimmed Hill. Not a full robust Hill implementation."""
    y = sorted_desc_positive(x)
    if k < 5 or y.size <= k:
        return np.nan
    r = int(math.floor(trim_frac * k))
    if r >= k - 2:
        return np.nan
    threshold = y[k]
    if threshold <= 0:
        return np.nan
    logs = np.log(y[r:k]) - math.log(threshold)
    gamma = float(np.mean(logs))
    if not np.isfinite(gamma) or gamma <= 0:
        return np.nan
    return 1.0 / gamma


def rank_half_alpha(x: np.ndarray, k: int) -> float:
    y = sorted_desc_positive(x)
    if k < 10 or y.size < k:
        return np.nan
    top = y[:k]
    if np.any(top <= 0):
        return np.nan
    ranks = np.arange(1, k + 1, dtype=float)
    yy = np.log(ranks - 0.5)
    xx = np.log(top)
    if np.unique(xx).size < 3:
        return np.nan
    slope, intercept = np.polyfit(xx, yy, 1)
    alpha = -float(slope)
    return alpha if np.isfinite(alpha) and alpha > 0 else np.nan


def gpd_mle_alpha(x: np.ndarray, k: int) -> Tuple[float, float, float, float]:
    """Fit GPD to top-k exceedances. Returns alpha, shape, scale, KS statistic."""
    y = sorted_desc_positive(x)
    if k < 10 or y.size <= k:
        return np.nan, np.nan, np.nan, np.nan
    u = y[k]
    exc = y[:k] - u
    exc = exc[np.isfinite(exc) & (exc > 0)]
    if exc.size < 10 or np.unique(exc).size < 5:
        return np.nan, np.nan, np.nan, np.nan
    try:
        shape, loc, scale = stats.genpareto.fit(exc, floc=0)
        if not np.isfinite(shape) or not np.isfinite(scale) or scale <= 0:
            return np.nan, np.nan, np.nan, np.nan
        if shape <= 1e-8:
            alpha = np.inf
        else:
            alpha = 1.0 / shape
        try:
            ks = float(stats.kstest(exc, "genpareto", args=(shape, 0.0, scale)).statistic)
        except Exception:
            ks = np.nan
        return float(alpha), float(shape), float(scale), ks
    except Exception:
        return np.nan, np.nan, np.nan, np.nan


def estimate_all_at_k(x: np.ndarray, k: int) -> Dict[str, float]:
    gpd_alpha, gpd_shape, gpd_scale, gpd_ks = gpd_mle_alpha(x, k)
    return {
        "alpha_hill": hill_alpha(x, k),
        "alpha_mom": mom_alpha(x, k),
        "alpha_gpd": gpd_alpha,
        "gpd_shape": gpd_shape,
        "gpd_scale": gpd_scale,
        "gpd_ks": gpd_ks,
        "alpha_pickands": pickands_alpha(x, k),
        "alpha_trimmed_hill": trimmed_hill_alpha(x, k),
        "alpha_rank_half": rank_half_alpha(x, k),
    }


def consensus_alpha_from_record(rec: Dict[str, float]) -> Tuple[float, float, int]:
    vals = []
    for key in ["alpha_hill", "alpha_mom", "alpha_gpd"]:
        v = rec.get(key, np.nan)
        if np.isfinite(v) and v > 0:
            vals.append(float(min(v, 100.0)))  # cap only for consensus stability
    if not vals:
        return np.nan, np.nan, 0
    med = float(np.median(vals))
    mad = float(np.median(np.abs(np.asarray(vals) - med))) if len(vals) > 1 else 0.0
    return med, mad, len(vals)


def k_grid_for_n(n_tail: int, min_k: int, k_min_frac: float, k_max_frac: float, step: int) -> List[int]:
    if n_tail <= 0:
        return []
    lo = max(min_k, int(math.floor(k_min_frac * n_tail)))
    hi = min(int(math.floor(k_max_frac * n_tail)), int(math.floor(n_tail / 4)), n_tail - 2)
    if hi < lo:
        return []
    return list(range(lo, hi + 1, max(1, step)))


def choose_adaptive_k(x: np.ndarray, cfg: TailConfig) -> Tuple[int, pd.DataFrame]:
    y = sorted_desc_positive(x)
    n_tail = y.size
    grid = k_grid_for_n(n_tail, cfg.min_k, cfg.k_min_frac, cfg.k_max_frac, cfg.adaptive_grid_step)
    if not grid:
        return -1, pd.DataFrame()

    records = []
    for k in grid:
        rec = {"k": k, "n_tail": n_tail, "k_frac": k / max(n_tail, 1)}
        rec.update(estimate_all_at_k(y, k))
        cons, disp, n_core = consensus_alpha_from_record(rec)
        rec["alpha_consensus_raw"] = cons
        rec["core_mad"] = disp
        rec["n_core_estimators"] = n_core
        records.append(rec)

    cand = pd.DataFrame(records)
    if cand.empty:
        return -1, cand

    # Local stability: rolling median absolute change of Hill and MOM around k.
    cand = cand.sort_values("k").reset_index(drop=True)
    for col in ["alpha_hill", "alpha_mom", "alpha_gpd"]:
        diff = cand[col].diff().abs()
        cand[f"{col}_local_change"] = diff.rolling(window=5, min_periods=1, center=True).median()

    def _score(row: pd.Series) -> float:
        cons = row["alpha_consensus_raw"]
        if not np.isfinite(cons) or cons <= 0 or row["n_core_estimators"] < 2:
            return np.inf
        rel_disp = row["core_mad"] / max(cons, 1e-9)
        local_vals = []
        for col in ["alpha_hill_local_change", "alpha_mom_local_change", "alpha_gpd_local_change"]:
            v = row.get(col, np.nan)
            if np.isfinite(v):
                local_vals.append(v / max(cons, 1e-9))
        local = float(np.nanmedian(local_vals)) if local_vals else 1.0
        ks = row.get("gpd_ks", np.nan)
        ks_pen = 0.0 if not np.isfinite(ks) else min(float(ks), 1.0)
        k_pen = 1.0 / math.sqrt(max(row["k"], 1))
        # Penalize extreme alpha from badly fitted GPD less than estimator disagreement.
        return 1.25 * rel_disp + 1.00 * local + 0.30 * ks_pen + 0.05 * k_pen

    cand["adaptive_score"] = cand.apply(_score, axis=1)
    finite = cand[np.isfinite(cand["adaptive_score"])]
    if finite.empty:
        # Fallback to 10% rule if adaptive fails.
        k_fallback = min(max(cfg.min_k, int(0.10 * n_tail)), n_tail - 2)
        return int(k_fallback), cand

    # Prefer a stable plateau not too close to the lower bound: among top 10% score,
    # choose median k to avoid an accidental single-k minimum.
    q = finite["adaptive_score"].quantile(0.10)
    plateau = finite[finite["adaptive_score"] <= q].sort_values("k")
    selected_k = int(plateau["k"].median()) if not plateau.empty else int(finite.loc[finite["adaptive_score"].idxmin(), "k"])
    return selected_k, cand


# -----------------------------------------------------------------------------
# Dependence and bootstrap
# -----------------------------------------------------------------------------

def circular_block_sample(arr: np.ndarray, block_len: int, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(arr, dtype=float)
    n = arr.size
    if n == 0:
        return arr.copy()
    block_len = max(1, min(int(block_len), n))
    n_blocks = int(math.ceil(n / block_len))
    starts = rng.integers(0, n, size=n_blocks)
    idx = []
    for s in starts:
        idx.extend(((s + np.arange(block_len)) % n).tolist())
    idx = np.asarray(idx[:n], dtype=int)
    return arr[idx]


def runs_extremal_index(r: np.ndarray, side: str, k: int, run_length: int) -> Tuple[float, int, int]:
    x_full = transform_tail(r, side, positive_only=False)
    x_pos = x_full[np.isfinite(x_full) & (x_full > 0)]
    y = sorted_desc_positive(x_pos)
    if k < 1 or y.size <= k:
        return np.nan, 0, 0
    u = y[k]
    exc = np.isfinite(x_full) & (x_full > u)
    n_exc = int(exc.sum())
    if n_exc == 0:
        return np.nan, 0, 0
    clusters = 0
    in_cluster = False
    zeros_since = run_length
    for flag in exc:
        if flag:
            if not in_cluster and zeros_since >= run_length:
                clusters += 1
                in_cluster = True
            zeros_since = 0
        else:
            zeros_since += 1
            if zeros_since >= run_length:
                in_cluster = False
    theta = clusters / n_exc if n_exc else np.nan
    return float(theta), clusters, n_exc


def bootstrap_alpha_ci(
    r_window: np.ndarray,
    side: str,
    selected_k: int,
    selected_k_frac: float,
    cfg: TailConfig,
    seed: int,
) -> Dict[str, float]:
    if cfg.bootstrap_reps <= 0:
        return {
            "boot_n": 0,
            "alpha_ci_low": np.nan,
            "alpha_ci_high": np.nan,
            "alpha_boot_mean": np.nan,
            "alpha_boot_std": np.nan,
            "p_alpha_lt_1": np.nan,
            "p_alpha_gt_2": np.nan,
        }

    rng = np.random.default_rng(seed)
    boot_vals = []
    block_lengths = cfg.block_lengths or [max(5, int(round(1.5 * (len(r_window) ** (1.0 / 3.0)))))]

    for b in range(cfg.bootstrap_reps):
        bl = int(block_lengths[b % len(block_lengths)])
        rb = circular_block_sample(r_window, bl, rng)
        xb = transform_tail(rb, side, positive_only=True)
        n_tail_b = xb.size
        if n_tail_b < cfg.min_tail_obs:
            continue
        if cfg.bootstrap_reselect_k:
            k_b, _ = choose_adaptive_k(xb, cfg)
        else:
            k_b = int(round(selected_k_frac * n_tail_b))
            k_b = max(cfg.min_k, min(k_b, n_tail_b - 2))
        if k_b < 2:
            continue
        rec = estimate_all_at_k(xb, k_b)
        cons, _, n_core = consensus_alpha_from_record(rec)
        if n_core >= 2 and np.isfinite(cons) and cons > 0:
            boot_vals.append(cons)

    arr = np.asarray(boot_vals, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return {
            "boot_n": 0,
            "alpha_ci_low": np.nan,
            "alpha_ci_high": np.nan,
            "alpha_boot_mean": np.nan,
            "alpha_boot_std": np.nan,
            "p_alpha_lt_1": np.nan,
            "p_alpha_gt_2": np.nan,
        }
    lo_q = (1.0 - cfg.ci_level) / 2.0
    hi_q = 1.0 - lo_q
    return {
        "boot_n": int(arr.size),
        "alpha_ci_low": float(np.quantile(arr, lo_q)),
        "alpha_ci_high": float(np.quantile(arr, hi_q)),
        "alpha_boot_mean": float(np.mean(arr)),
        "alpha_boot_std": float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0,
        "p_alpha_lt_1": float(np.mean(arr < 1.0)),
        "p_alpha_gt_2": float(np.mean(arr > 2.0)),
    }


def assign_tail_group(row: pd.Series, cfg: TailConfig) -> str:
    alpha = row.get("alpha_consensus", np.nan)
    ci_low = row.get("alpha_ci_low", np.nan)
    ci_high = row.get("alpha_ci_high", np.nan)
    p_lt1 = row.get("p_alpha_lt_1", np.nan)
    p_gt2 = row.get("p_alpha_gt_2", np.nan)

    strict_lt1 = False
    strict_gt2 = False
    middle = False

    if np.isfinite(ci_high) and ci_high < 1.0:
        strict_lt1 = True
    if np.isfinite(p_lt1) and p_lt1 >= cfg.strict_prob:
        strict_lt1 = True

    if np.isfinite(ci_low) and ci_low > 2.0:
        strict_gt2 = True
    if np.isfinite(p_gt2) and p_gt2 >= cfg.strict_prob:
        strict_gt2 = True

    if np.isfinite(ci_low) and np.isfinite(ci_high) and ci_low >= 1.0 and ci_high <= 2.0:
        middle = True

    if strict_lt1 and not strict_gt2:
        return "strict_alpha_lt_1"
    if strict_gt2 and not strict_lt1:
        return "strict_alpha_gt_2"
    if middle:
        return "strict_alpha_1_2"
    if np.isfinite(alpha):
        if alpha < 1.0:
            return "point_alpha_lt_1_uncertain"
        if alpha > 2.0:
            return "point_alpha_gt_2_uncertain"
        return "point_alpha_1_2_uncertain"
    return "unclassified"


# -----------------------------------------------------------------------------
# Per-security rolling estimation
# -----------------------------------------------------------------------------

def estimate_security_windows(args: Tuple[str, str, pd.DataFrame, Dict]) -> List[Dict[str, object]]:
    market, secid, g, cfg_dict = args
    cfg = TailConfig(**cfg_dict)
    g = g.sort_values("tradedate")
    dates = g["tradedate"].to_numpy()
    returns = g["model_return"].to_numpy(dtype=float)
    log_returns = g["log_return"].to_numpy(dtype=float)

    out_rows: List[Dict[str, object]] = []
    rng = np.random.default_rng(cfg.random_seed + abs(hash((market, secid))) % (2**31 - 1))

    for window in tqdm(cfg.windows):
        if returns.size < window:
            continue
        starts = list(range(0, returns.size - window + 1, cfg.step))
        # Ensure the last possible window is included.
        last_start = returns.size - window
        if starts and starts[-1] != last_start:
            starts.append(last_start)
        elif not starts:
            starts = [last_start]

        for start in tqdm(starts):
            end = start + window
            r_win = returns[start:end]
            raw_win = log_returns[start:end]
            date_start = pd.Timestamp(dates[start])
            date_end = pd.Timestamp(dates[end - 1])

            valid = np.isfinite(r_win)
            if int(valid.sum()) < window * 0.80:
                continue
            r_eff = r_win[valid]
            x = transform_tail(r_eff, cfg.tail_side, positive_only=True)
            n_tail = int(x.size)
            if n_tail < cfg.min_tail_obs:
                continue

            selected_k, cand = choose_adaptive_k(x, cfg)
            if selected_k <= 0:
                continue

            rec = estimate_all_at_k(x, selected_k)
            alpha_cons, alpha_mad, n_core = consensus_alpha_from_record(rec)
            selected_k_frac = selected_k / max(n_tail, 1)

            theta, n_clusters, n_exc = runs_extremal_index(r_eff, cfg.tail_side, selected_k, cfg.theta_run_length)

            boot_seed = int(rng.integers(0, 2**31 - 1))
            boot = bootstrap_alpha_ci(r_eff, cfg.tail_side, selected_k, selected_k_frac, cfg, boot_seed)

            row: Dict[str, object] = {
                "market": market,
                "secid": secid,
                "window": window,
                "window_start": date_start,
                "window_end": date_end,
                "n_obs_window": int(valid.sum()),
                "n_tail_positive": n_tail,
                "tail_side": cfg.tail_side,
                "filter_method": cfg.filter_method,
                "selected_k": int(selected_k),
                "selected_k_frac": float(selected_k_frac),
                "alpha_consensus": alpha_cons,
                "alpha_core_mad": alpha_mad,
                "n_core_estimators": n_core,
                "theta_runs": theta,
                "theta_clusters": int(n_clusters),
                "theta_exceedances": int(n_exc),
                "mean_return_window": float(np.nanmean(raw_win)),
                "std_return_window": float(np.nanstd(raw_win, ddof=1)) if np.isfinite(raw_win).sum() > 1 else np.nan,
                "zero_share_window": float(np.mean(np.abs(raw_win[np.isfinite(raw_win)]) <= cfg.zero_tol)) if np.isfinite(raw_win).sum() else np.nan,
                "max_loss_window": float(np.nanmax(transform_tail(raw_win, "lower", positive_only=False))) if np.isfinite(raw_win).sum() else np.nan,
            }
            row.update(rec)
            row.update(boot)

            # Diagnostics from the candidate grid around selected k.
            if cand is not None and not cand.empty:
                sel = cand.iloc[(cand["k"] - selected_k).abs().argsort()[:1]]
                if not sel.empty:
                    row["adaptive_score"] = float(sel["adaptive_score"].iloc[0]) if "adaptive_score" in sel else np.nan
                row["adaptive_grid_k_min"] = int(cand["k"].min())
                row["adaptive_grid_k_max"] = int(cand["k"].max())
                row["adaptive_grid_n"] = int(cand.shape[0])
                # Store a compact stability summary, not the full grid.
                finite_alpha = cand["alpha_consensus_raw"].replace([np.inf, -np.inf], np.nan).dropna()
                row["adaptive_alpha_grid_median"] = float(finite_alpha.median()) if not finite_alpha.empty else np.nan
                row["adaptive_alpha_grid_iqr"] = float(finite_alpha.quantile(0.75) - finite_alpha.quantile(0.25)) if finite_alpha.size >= 4 else np.nan

            # Tail group based on CI / bootstrap probabilities.
            tmp = pd.Series(row)
            row["tail_group"] = assign_tail_group(tmp, cfg)
            out_rows.append(row)

    return out_rows


# -----------------------------------------------------------------------------
# Summaries and plotting
# -----------------------------------------------------------------------------

def summarize_estimates(est: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if est.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    group_counts = (
        est.groupby(["market", "window", "window_end", "tail_group"])
        .size()
        .reset_index(name="n")
        .sort_values(["market", "window", "window_end", "tail_group"])
    )

    est_cols = ["alpha_consensus", "alpha_hill", "alpha_mom", "alpha_gpd", "alpha_pickands", "alpha_trimmed_hill", "alpha_rank_half"]
    summary_rows = []
    for keys, g in est.groupby(["market", "window", "tail_side", "filter_method"]):
        d = dict(zip(["market", "window", "tail_side", "filter_method"], keys))
        d["n_estimates"] = len(g)
        d["n_securities"] = g["secid"].nunique()
        for col in est_cols:
            vals = pd.to_numeric(g[col], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
            d[f"{col}_mean"] = vals.mean() if not vals.empty else np.nan
            d[f"{col}_median"] = vals.median() if not vals.empty else np.nan
            d[f"{col}_p10"] = vals.quantile(0.10) if not vals.empty else np.nan
            d[f"{col}_p90"] = vals.quantile(0.90) if not vals.empty else np.nan
        summary_rows.append(d)
    estimator_summary = pd.DataFrame(summary_rows)

    # Latest membership per security and window.
    idx = est.sort_values("window_end").groupby(["market", "secid", "window"]).tail(1).index
    latest = est.loc[idx].sort_values(["market", "window", "tail_group", "secid"])
    latest_cols = [
        "market", "secid", "window", "window_end", "tail_group", "alpha_consensus",
        "alpha_ci_low", "alpha_ci_high", "p_alpha_lt_1", "p_alpha_gt_2", "selected_k",
        "n_tail_positive", "theta_runs", "zero_share_window", "max_loss_window",
        "alpha_hill", "alpha_mom", "alpha_gpd", "alpha_pickands", "alpha_rank_half",
    ]
    latest = latest[[c for c in latest_cols if c in latest.columns]]

    return group_counts, estimator_summary, latest


def diagnostic_candidates(est: pd.DataFrame, n_each: int = 10) -> pd.DataFrame:
    if est.empty:
        return pd.DataFrame()
    latest = est.sort_values("window_end").groupby(["market", "secid", "window"]).tail(1).copy()
    latest["ci_width"] = latest["alpha_ci_high"] - latest["alpha_ci_low"]
    latest["dist_to_1"] = (latest["alpha_consensus"] - 1.0).abs()
    latest["dist_to_2"] = (latest["alpha_consensus"] - 2.0).abs()
    latest["dist_to_cutoff"] = latest[["dist_to_1", "dist_to_2"]].min(axis=1)

    parts = []
    for (market, window), g in latest.groupby(["market", "window"]):
        stable = g.sort_values(["ci_width", "alpha_core_mad"]).head(n_each).assign(diagnostic_bucket="stable_low_uncertainty")
        boundary = g.sort_values("dist_to_cutoff").head(n_each).assign(diagnostic_bucket="near_cutoff")
        unstable = g.sort_values(["ci_width", "alpha_core_mad"], ascending=False).head(n_each).assign(diagnostic_bucket="unstable_high_uncertainty")
        parts.extend([stable, boundary, unstable])
    out = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    cols = [
        "diagnostic_bucket", "market", "secid", "window", "window_end", "tail_group",
        "alpha_consensus", "alpha_ci_low", "alpha_ci_high", "ci_width", "alpha_core_mad",
        "selected_k", "n_tail_positive", "theta_runs", "zero_share_window", "max_loss_window",
    ]
    return out[[c for c in cols if c in out.columns]].drop_duplicates()


def make_plots(est: pd.DataFrame, outdir: str) -> None:
    if est.empty:
        return
    try:
        import matplotlib.pyplot as plt
    except Exception:
        return

    figdir = os.path.join(outdir, "figures")
    ensure_dir(figdir)

    plot_df = est.replace([np.inf, -np.inf], np.nan).dropna(subset=["alpha_consensus"])
    if plot_df.empty:
        return

    for (market, window), g in plot_df.groupby(["market", "window"]):
        plt.figure(figsize=(10, 6))
        vals = g["alpha_consensus"].clip(upper=10)
        plt.hist(vals, bins=40)
        plt.axvline(1.0, linestyle="--")
        plt.axvline(2.0, linestyle="--")
        plt.title(f"Consensus tail-index distribution: {market}, window={window}")
        plt.xlabel("alpha consensus, capped at 10")
        plt.ylabel("Count")
        plt.tight_layout()
        plt.savefig(os.path.join(figdir, f"alpha_hist_{market}_w{window}.png"), dpi=150)
        plt.close()

        # Cross-sectional median over time.
        med = g.groupby("window_end")["alpha_consensus"].median().reset_index()
        if len(med) > 1:
            plt.figure(figsize=(12, 6))
            plt.plot(med["window_end"], med["alpha_consensus"])
            plt.axhline(1.0, linestyle="--")
            plt.axhline(2.0, linestyle="--")
            plt.title(f"Rolling median alpha: {market}, window={window}")
            plt.xlabel("Window end")
            plt.ylabel("Median consensus alpha")
            plt.tight_layout()
            plt.savefig(os.path.join(figdir, f"alpha_median_ts_{market}_w{window}.png"), dpi=150)
            plt.close()

    # Group counts over time.
    counts = est.groupby(["market", "window", "window_end", "tail_group"]).size().reset_index(name="n")
    for (market, window), g in counts.groupby(["market", "window"]):
        piv = g.pivot_table(index="window_end", columns="tail_group", values="n", fill_value=0)
        if piv.shape[0] <= 1:
            continue
        plt.figure(figsize=(12, 6))
        for col in piv.columns:
            plt.plot(piv.index, piv[col], label=col)
        plt.title(f"Tail-group counts: {market}, window={window}")
        plt.xlabel("Window end")
        plt.ylabel("Number of securities")
        plt.legend(fontsize=8)
        plt.tight_layout()
        plt.savefig(os.path.join(figdir, f"tail_group_counts_{market}_w{window}.png"), dpi=150)
        plt.close()


def write_memo(cfg: TailConfig, audit: pd.DataFrame, uni: pd.DataFrame, selected: pd.DataFrame, est: pd.DataFrame, outdir: str) -> None:
    lines = []
    lines.append("# Stage 4 tail-index memo\n")
    lines.append("## Configuration\n")
    lines.append(f"- Table: `{cfg.table}`")
    lines.append(f"- Markets: {', '.join(cfg.markets)}")
    lines.append(f"- Period: {cfg.start_date or 'start'} to {cfg.end_date or 'end'}")
    lines.append(f"- Tail side: `{cfg.tail_side}`")
    lines.append(f"- Filter method: `{cfg.filter_method}`")
    lines.append(f"- Windows: {cfg.windows}; step={cfg.step}")
    lines.append(f"- Bootstrap reps: {cfg.bootstrap_reps}; block lengths={cfg.block_lengths}")
    lines.append(f"- Universe: {'core_liquid' if cfg.core_universe else 'broad'}\n")

    lines.append("## Data audit\n")
    for _, row in audit.iterrows():
        lines.append(f"- {row['item']}: {row['value']}")

    lines.append("\n## Universe\n")
    if not uni.empty:
        u_summary = uni.groupby("market").agg(
            securities=("secid", "nunique"),
            core_liquid=("core_liquid", "sum"),
            broad=("broad", "sum"),
            median_coverage=("coverage", "median"),
            median_zero_share=("zero_share", "median"),
        ).reset_index()
        lines.append(u_summary.to_markdown(index=False))
    lines.append("\nSelected securities:")
    if not selected.empty:
        lines.append(selected.groupby("market")["secid"].nunique().reset_index(name="n").to_markdown(index=False))
    else:
        lines.append("No securities selected. Relax universe filters.")

    lines.append("\n## Estimation results\n")
    if est.empty:
        lines.append("No tail-index estimates were produced. Check window length, min_tail_obs, and universe filters.")
    else:
        lines.append(f"Total rolling estimates: {len(est)}")
        lines.append(f"Securities with estimates: {est[['market', 'secid']].drop_duplicates().shape[0]}")
        gc = est.groupby(["market", "window", "tail_group"]).size().reset_index(name="n")
        lines.append(gc.to_markdown(index=False))
        lines.append("\nInterpretation rule: strict_alpha_lt_1 and strict_alpha_gt_2 are the defensible groups for the main DQ-vs-DR hypothesis. Point-estimate uncertain groups should be used only for robustness or continuous-alpha tests.")

    with open(os.path.join(outdir, "research_tail_stage4_memo.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def parse_args() -> TailConfig:
    p = argparse.ArgumentParser(description="Robust rolling tail-index estimation for MOEX returns")
    p.add_argument("--db-url", default="postgresql://postgres:password2544@localhost:5432/heavy_tails_data")
    p.add_argument("--table", default="moex_total_return_daily")
    p.add_argument("--outdir", default="moex_tail_stage4_outputs")
    p.add_argument("--markets", nargs="+", default=["shares", "bonds"])
    p.add_argument("--start-date", default="2018-01-01")
    p.add_argument("--end-date", default=None)
    p.add_argument("--windows", nargs="+", type=int, default=[252, 504])
    p.add_argument("--step", type=int, default=21)
    p.add_argument("--tail-side", choices=["lower", "upper", "abs"], default="lower")
    p.add_argument("--filter-method", choices=["raw", "ewma"], default="raw")
    p.add_argument("--ewma-span", type=int, default=60)

    p.add_argument("--universe", choices=["core", "broad"], default="core")
    p.add_argument("--min-obs-core", type=int, default=750)
    p.add_argument("--min-obs-broad", type=int, default=500)
    p.add_argument("--coverage-core-shares", type=float, default=0.95)
    p.add_argument("--coverage-core-bonds", type=float, default=0.95)
    p.add_argument("--coverage-broad-shares", type=float, default=0.90)
    p.add_argument("--coverage-broad-bonds", type=float, default=0.90)
    p.add_argument("--zero-share-core-shares", type=float, default=0.20)
    p.add_argument("--zero-share-core-bonds", type=float, default=0.35)
    p.add_argument("--zero-share-broad-shares", type=float, default=0.25)
    p.add_argument("--zero-share-broad-bonds", type=float, default=0.50)
    p.add_argument("--zero-tol", type=float, default=1e-12)

    p.add_argument("--min-tail-obs", type=int, default=80)
    p.add_argument("--min-k", type=int, default=10)
    p.add_argument("--k-min-frac", type=float, default=0.02)
    p.add_argument("--k-max-frac", type=float, default=0.15)
    p.add_argument("--adaptive-grid-step", type=int, default=1)

    p.add_argument("--bootstrap-reps", type=int, default=200)
    p.add_argument("--block-lengths", nargs="+", type=int, default=[5, 10, 15])
    p.add_argument("--bootstrap-reselect-k", action="store_true")
    p.add_argument("--ci-level", type=float, default=0.90)
    p.add_argument("--strict-prob", type=float, default=0.95)
    p.add_argument("--theta-run-length", type=int, default=5)
    p.add_argument("--theta-declustering-cutoff", type=float, default=0.80)

    p.add_argument("--max-securities-per-market", type=int, default=None)
    p.add_argument("--random-seed", type=int, default=42)
    p.add_argument("--n-jobs", type=int, default=1)
    p.add_argument("--max-abs-return-for-audit", type=float, default=0.75)

    p.add_argument("--db-write-intermediate", action="store_true",
                   help="Append per-security completed estimates to PostgreSQL during stage [5/8].")
    p.add_argument("--db-results-table", default="stage4_tail_alpha_estimates",
                   help="Target table for per-security rolling estimates; table or schema.table.")
    p.add_argument("--db-progress-table", default="stage4_tail_security_progress",
                   help="Checkpoint/progress table; table or schema.table.")
    p.add_argument("--db-chunksize", type=int, default=5000)
    p.add_argument("--run-id", default=None,
                   help="Run identifier written to DB. Default: UTC timestamp.")

    a = p.parse_args()
    run_id = a.run_id or datetime.now(timezone.utc).strftime("stage4_%Y%m%dT%H%M%SZ")
    return TailConfig(
        db_url=a.db_url,
        table=a.table,
        outdir=a.outdir,
        markets=[m.lower() for m in a.markets],
        start_date=a.start_date,
        end_date=a.end_date,
        windows=a.windows,
        step=a.step,
        tail_side=a.tail_side,
        filter_method=a.filter_method,
        ewma_span=a.ewma_span,
        core_universe=(a.universe == "core"),
        min_obs_core=a.min_obs_core,
        min_obs_broad=a.min_obs_broad,
        coverage_core_shares=a.coverage_core_shares,
        coverage_core_bonds=a.coverage_core_bonds,
        coverage_broad_shares=a.coverage_broad_shares,
        coverage_broad_bonds=a.coverage_broad_bonds,
        zero_share_core_shares=a.zero_share_core_shares,
        zero_share_core_bonds=a.zero_share_core_bonds,
        zero_share_broad_shares=a.zero_share_broad_shares,
        zero_share_broad_bonds=a.zero_share_broad_bonds,
        zero_tol=a.zero_tol,
        min_tail_obs=a.min_tail_obs,
        min_k=a.min_k,
        k_min_frac=a.k_min_frac,
        k_max_frac=a.k_max_frac,
        adaptive_grid_step=a.adaptive_grid_step,
        bootstrap_reps=a.bootstrap_reps,
        block_lengths=a.block_lengths,
        bootstrap_reselect_k=a.bootstrap_reselect_k,
        ci_level=a.ci_level,
        strict_prob=a.strict_prob,
        theta_run_length=a.theta_run_length,
        theta_declustering_cutoff=a.theta_declustering_cutoff,
        max_securities_per_market=a.max_securities_per_market,
        random_seed=a.random_seed,
        n_jobs=a.n_jobs,
        max_abs_return_for_audit=a.max_abs_return_for_audit,
        db_write_intermediate=a.db_write_intermediate,
        db_results_table=a.db_results_table,
        db_progress_table=a.db_progress_table,
        db_chunksize=a.db_chunksize,
        run_id=run_id,
    )


def main() -> None:
    cfg = parse_args()
    ensure_dir(cfg.outdir)
    ensure_dir(os.path.join(cfg.outdir, "figures"))

    with open(os.path.join(cfg.outdir, "00_tail_config.json"), "w", encoding="utf-8") as f:
        json.dump(asdict(cfg), f, ensure_ascii=False, indent=2, default=str)

    print("[1/8] Loading data...")
    raw = load_returns(cfg)
    raw_rows = len(raw)
    print(f"      rows loaded: {raw_rows:,}")

    print("[2/8] Choosing canonical boards...")
    canonical, board_map = choose_canonical_boards(raw)
    canonical = canonical.dropna(subset=["log_return"]).copy()
    canonical = canonical[np.isfinite(canonical["log_return"])]

    print("[3/8] Applying filter method...")
    canonical = apply_filter_method(canonical, cfg)
    canonical = canonical.dropna(subset=["model_return"]).copy()
    canonical = canonical[np.isfinite(canonical["model_return"])]

    audit = make_data_audit(raw, canonical, board_map, cfg)
    audit.to_csv(os.path.join(cfg.outdir, "01_data_audit.csv"), index=False)
    board_map.to_csv(os.path.join(cfg.outdir, "01_board_selection_audit.csv"), index=False)

    print("[4/8] Building universe...")
    universe, selected = build_universe(canonical, cfg)
    universe.to_csv(os.path.join(cfg.outdir, "02_universe_summary.csv"), index=False)
    selected.to_csv(os.path.join(cfg.outdir, "02_selected_universe.csv"), index=False)
    print(selected.groupby("market")["secid"].nunique().reset_index(name="selected_n").to_string(index=False) if not selected.empty else "No selected securities")

    if selected.empty:
        write_memo(cfg, audit, universe, selected, pd.DataFrame(), cfg.outdir)
        print("No securities selected. Relax filters or use --universe broad.")
        return

    selected_keys = set(zip(selected["market"], selected["secid"]))
    work_df = canonical[canonical[["market", "secid"]].apply(tuple, axis=1).isin(selected_keys)].copy()

    print("[5/8] Estimating rolling tail-indexes...")
    tasks = []
    cfg_dict = asdict(cfg)
    for (market, secid), g in work_df.groupby(["market", "secid"], sort=False):
        tasks.append((market, secid, g[["tradedate", "log_return", "model_return"]].copy(), cfg_dict))

    if cfg.db_write_intermediate:
        init_intermediate_db_tables(cfg)
        print(f"      DB checkpoints enabled: run_id={cfg.run_id}")
        print(f"      results table: {cfg.db_results_table}")
        print(f"      progress table: {cfg.db_progress_table}")

    rows: List[Dict[str, object]] = []
    if cfg.n_jobs and cfg.n_jobs > 1:
        with ProcessPoolExecutor(max_workers=cfg.n_jobs) as ex:
            future_to_security = {
                ex.submit(estimate_security_windows, t): (t[0], t[1])
                for t in tasks
            }
            for i, fut in enumerate(tqdm(as_completed(future_to_security)), 1):
                market, secid = future_to_security[fut]
                try:
                    security_rows = fut.result()
                    rows.extend(security_rows)
                    if cfg.db_write_intermediate:
                        write_security_checkpoint_to_db(cfg, security_rows, market, secid, status="done")
                    print(f"      checkpoint {market}:{secid}; estimates={len(security_rows):,}")
                except Exception as e:
                    print(f"      worker failed for {market}:{secid}: {e}")
                    if cfg.db_write_intermediate:
                        write_security_checkpoint_to_db(cfg, [], market, secid, status="failed", error=str(e))
                if i % 25 == 0 or i == len(future_to_security):
                    print(f"      completed {i}/{len(future_to_security)} securities; estimates={len(rows):,}")
    else:
        for i, t in enumerate(tqdm(tasks), 1):
            market, secid = t[0], t[1]
            try:
                security_rows = estimate_security_windows(t)
                rows.extend(security_rows)
                if cfg.db_write_intermediate:
                    write_security_checkpoint_to_db(cfg, security_rows, market, secid, status="done")
                print(f"      checkpoint {market}:{secid}; estimates={len(security_rows):,}")
            except Exception as e:
                print(f"      worker failed for {market}:{secid}: {e}")
                if cfg.db_write_intermediate:
                    write_security_checkpoint_to_db(cfg, [], market, secid, status="failed", error=str(e))
            if i % 25 == 0 or i == len(tasks):
                print(f"      completed {i}/{len(tasks)} securities; estimates={len(rows):,}")

    est = pd.DataFrame(rows)
    if not est.empty:
        # Convert datetimes cleanly for CSV/parquet.
        est["window_start"] = pd.to_datetime(est["window_start"])
        est["window_end"] = pd.to_datetime(est["window_end"])
    save_table(est, os.path.join(cfg.outdir, "03_tail_alpha_estimates"))

    print("[6/8] Summarizing...")
    group_counts, estimator_summary, latest = summarize_estimates(est)
    group_counts.to_csv(os.path.join(cfg.outdir, "04_tail_group_counts.csv"), index=False)
    estimator_summary.to_csv(os.path.join(cfg.outdir, "05_estimator_summary.csv"), index=False)
    latest.to_csv(os.path.join(cfg.outdir, "06_group_membership_latest.csv"), index=False)
    diagnostic_candidates(est).to_csv(os.path.join(cfg.outdir, "07_diagnostic_candidates.csv"), index=False)

    print("[7/8] Plotting...")
    make_plots(est, cfg.outdir)

    print("[8/8] Writing memo...")
    write_memo(cfg, audit, universe, selected, est, cfg.outdir)

    print("Done.")
    print(f"Outputs are in: {cfg.outdir}")
    if not est.empty:
        print("Main file: 03_tail_alpha_estimates.csv")
        print("Latest group membership: 06_group_membership_latest.csv")
        print("Memo: research_tail_stage4_memo.md")


if __name__ == "__main__":
    main()
