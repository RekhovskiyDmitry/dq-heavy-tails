#!/usr/bin/env python3
"""Audit coursework data claims directly from the archived research bundle.

This intentionally reads the canonical ZIP archive in-place instead of relying
on generated local `article/tables/*.csv` files. The archive still stores the
research outputs as CSV internally, but the source of truth is the bundled
archive, not the derived manuscript tables.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "moex_article_core_assetwise_20260524_1008.zip"
STANDALONE_STAGE6 = ROOT / "moex_stage6_article_digest.zip"
REPORT = ROOT / "docs" / "ARCHIVE_DATA_AUDIT_2026-06-02.md"

PREFIX = "moex_article_core_bundle_assetwise"
TAIL = f"{PREFIX}/moex_tail_stage4_main_shares_raw"
STAGE2 = f"{PREFIX}/moex_stage2_alpha_windows_shares_parallel"
STAGE5 = f"{PREFIX}/moex_stage5_alpha_windows_shares_assetwise"
STAGE6 = f"{PREFIX}/moex_stage6_article_digest_assetwise"


def read_csv_from_zip(zf: zipfile.ZipFile, name: str) -> list[dict[str, str]]:
    text = zf.read(name).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(text)))


def f(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if value == "":
        return math.nan
    if value == "Infinity":
        return math.inf
    return float(value)


def mean_skip_missing(values: list[str]) -> float:
    nums = [f(v) for v in values]
    nums = [x for x in nums if not math.isnan(x)]
    if not nums:
        return math.nan
    return sum(nums) / len(nums)


def fmt(value: float, digits: int = 12) -> str:
    if math.isfinite(value):
        return f"{value:.{digits}g}"
    return str(value)


def quantile(values: list[float], q: float) -> float:
    if not values:
        raise ValueError("empty quantile input")
    values = sorted(values)
    pos = (len(values) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return values[lo]
    return values[lo] * (hi - pos) + values[hi] * (pos - lo)


def close(a: object, b: object, tol: float = 1e-9) -> bool:
    try:
        return abs(f(a) - f(b)) <= tol
    except Exception:
        return str(a) == str(b)


def median(values: list[float]) -> float:
    return statistics.median(values)


def digest_by_key(
    rows: list[dict[str, str]], key_cols: list[str]
) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row[col] for col in key_cols): row for row in rows}


def check_rows(
    name: str,
    expected: list[dict[str, object]],
    actual: list[dict[str, str]],
    key_cols: list[str],
    value_cols: list[str],
    tol: float = 1e-9,
) -> tuple[list[str], list[str]]:
    notes: list[str] = []
    failures: list[str] = []
    actual_map = digest_by_key(actual, key_cols)
    for exp in expected:
        key = tuple(str(exp[col]) for col in key_cols)
        row = actual_map.get(key)
        if row is None:
            failures.append(f"{name}: missing row {key}")
            continue
        for col in value_cols:
            if not close(exp[col], row[col], tol=tol):
                failures.append(
                    f"{name}: {key} {col} expected {exp[col]!r}, archive digest has {row[col]!r}"
                )
    notes.append(f"{name}: checked {len(expected)} rows against archive digest")
    return notes, failures


def tail_alpha_summary(raw: list[dict[str, str]]) -> list[dict[str, object]]:
    out = []
    for window in sorted({r["window"] for r in raw}, key=int):
        rows = [r for r in raw if r["window"] == window]
        alphas = [f(r["alpha_consensus"]) for r in rows]
        groups = Counter(r["tail_group"] for r in rows)
        out.append(
            {
                "window": window,
                "n_estimates": len(rows),
                "n_securities": len({r["secid"] for r in rows}),
                "alpha_mean": sum(alphas) / len(alphas),
                "alpha_median": median(alphas),
                "alpha_p10": quantile(alphas, 0.10),
                "alpha_p25": quantile(alphas, 0.25),
                "alpha_p75": quantile(alphas, 0.75),
                "alpha_p90": quantile(alphas, 0.90),
                "point_alpha_lt1": sum(a < 1 for a in alphas),
                "point_alpha_1_2": sum(1 <= a < 2 for a in alphas),
                "point_alpha_gt2": sum(a > 2 for a in alphas),
                "strict_alpha_lt1": groups["strict_alpha_lt_1"],
                "strict_alpha_1_2": groups["strict_alpha_1_2"],
                "strict_alpha_gt2": groups["strict_alpha_gt_2"],
                "mean_p_alpha_lt1": mean_skip_missing(
                    [r["p_alpha_lt_1"] for r in rows]
                ),
                "mean_p_alpha_gt2": mean_skip_missing(
                    [r["p_alpha_gt_2"] for r in rows]
                ),
            }
        )
    return out


def latest_tail_summary(raw: list[dict[str, str]]) -> list[dict[str, object]]:
    out = []
    for window in sorted({r["window"] for r in raw}, key=int):
        rows = [r for r in raw if r["window"] == window]
        alphas = [f(r["alpha_consensus"]) for r in rows]
        groups = Counter(r["tail_group"] for r in rows)
        out.append(
            {
                "window": window,
                "n_securities": len({r["secid"] for r in rows}),
                "alpha_median": median(alphas),
                "alpha_p10": quantile(alphas, 0.10),
                "alpha_p25": quantile(alphas, 0.25),
                "alpha_p75": quantile(alphas, 0.75),
                "point_alpha_lt1": sum(a < 1 for a in alphas),
                "point_alpha_1_2": sum(1 <= a < 2 for a in alphas),
                "point_alpha_gt2": sum(a > 2 for a in alphas),
                "strict_alpha_lt1": groups["strict_alpha_lt_1"],
                "strict_alpha_1_2": groups["strict_alpha_1_2"],
                "strict_alpha_gt2": groups["strict_alpha_gt_2"],
                "point_alpha_1_2_uncertain": groups["point_alpha_1_2_uncertain"],
                "point_alpha_gt_2_uncertain": groups["point_alpha_gt_2_uncertain"],
                "point_alpha_lt_1_uncertain": groups["point_alpha_lt_1_uncertain"],
                "mean_p_alpha_lt1": mean_skip_missing(
                    [r["p_alpha_lt_1"] for r in rows]
                ),
                "mean_p_alpha_gt2": mean_skip_missing(
                    [r["p_alpha_gt_2"] for r in rows]
                ),
            }
        )
    return out


def horserace_summary(reg: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = [
        r
        for r in reg
        if r["param"] in {"dq_es", "dr_es_concentration", "current_es", "current_rv_ann", "current_var"}
    ]
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["dependent"], row["spec_name"], row["param"])].append(row)
    out = []
    for key in sorted(grouped):
        vals = grouped[key]
        coefs = [f(r["coef"]) for r in vals]
        tvals = [f(r["t_hac"]) for r in vals]
        r2s = [f(r["r2"]) for r in vals]
        sig10_rows = [r for r in vals if f(r["pvalue_hac"]) < 0.10]
        sig5_rows = [r for r in vals if f(r["pvalue_hac"]) < 0.05]
        out.append(
            {
                "dependent": key[0],
                "spec_name": key[1],
                "param": key[2],
                "n_models": len(vals),
                "sig10": len(sig10_rows),
                "sig5": len(sig5_rows),
                "pos_sig10": sum(f(r["coef"]) > 0 for r in sig10_rows),
                "neg_sig10": sum(f(r["coef"]) < 0 for r in sig10_rows),
                "median_coef": median(coefs),
                "median_t_hac": median(tvals),
                "mean_r2": sum(r2s) / len(r2s),
            }
        )
    return out


def stage5_summary(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows = [
        r
        for r in rows
        if r["status"] == "ok" and r["param"] in {"z_dq_x_heavy", "z_dr_x_heavy"}
    ]
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["dependent"], row["spec"], row["param"])].append(row)
    out = []
    for key in sorted(grouped):
        vals = grouped[key]
        coefs = [f(r["coef"]) for r in vals]
        tvals = [f(r["t_hac"]) for r in vals]
        r2s = [f(r["r2"]) for r in vals]
        pvals = [f(r["pvalue_hac"]) for r in vals]
        sig10_rows = [r for r in vals if f(r["pvalue_hac"]) < 0.10]
        sig5_rows = [r for r in vals if f(r["pvalue_hac"]) < 0.05]
        out.append(
            {
                "dependent": key[0],
                "spec": key[1],
                "param": key[2],
                "n_models": len(vals),
                "sig10": len(sig10_rows),
                "sig5": len(sig5_rows),
                "pos_sig10": sum(f(r["coef"]) > 0 for r in sig10_rows),
                "neg_sig10": sum(f(r["coef"]) < 0 for r in sig10_rows),
                "median_coef": median(coefs),
                "median_t_hac": median(tvals),
                "mean_r2": sum(r2s) / len(r2s),
                "min_pvalue": min(pvals),
            }
        )
    return out


def sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def compare_standalone_stage6(zf: zipfile.ZipFile) -> list[str]:
    notes = []
    if not STANDALONE_STAGE6.exists():
        return ["standalone Stage6 digest archive not found"]
    with zipfile.ZipFile(STANDALONE_STAGE6) as other:
        for base in [
            "01_tail_alpha_summary.csv",
            "02_latest_tail_group_summary.csv",
            "03_stage2_horserace_summary.csv",
            "04_stage2_future_tail_event_main_table.csv",
            "05_stage5_interaction_summary.csv",
            "06_key_correlations.csv",
        ]:
            assetwise_name = f"{STAGE6}/{base}"
            standalone_name = f"moex_stage6_article_digest/{base}"
            a_hash = sha12(zf.read(assetwise_name))
            s_hash = sha12(other.read(standalone_name))
            status = "MATCH" if a_hash == s_hash else "DIFF"
            notes.append(f"{base}: assetwise {a_hash}, standalone {s_hash} -> {status}")
    return notes


def main() -> int:
    failures: list[str] = []
    notes: list[str] = []

    with zipfile.ZipFile(ARCHIVE) as zf:
        archive_files = zf.namelist()
        notes.append(f"canonical archive: {ARCHIVE.name}")
        notes.append(f"archive entries: {len(archive_files)}")

        tail_raw = read_csv_from_zip(zf, f"{TAIL}/03_tail_alpha_estimates.csv")
        latest_raw = read_csv_from_zip(zf, f"{TAIL}/06_group_membership_latest.csv")
        stage2_reg = read_csv_from_zip(zf, f"{STAGE2}/04_stage2_regressions_hac.csv")
        stage5_reg = read_csv_from_zip(zf, f"{STAGE5}/02_alpha_interaction_regressions.csv")
        stage5_corr = read_csv_from_zip(zf, f"{STAGE5}/04_alpha_signal_correlations.csv")

        notes.append(f"Stage4 raw tail estimates rows: {len(tail_raw)}")
        notes.append(f"Stage4 latest membership rows: {len(latest_raw)}")
        notes.append(f"Stage2 HAC regression rows: {len(stage2_reg)}")
        notes.append(f"Stage5 interaction regression rows: {len(stage5_reg)}")
        notes.append(f"Stage5 correlation rows: {len(stage5_corr)}")

        tail_digest = read_csv_from_zip(zf, f"{STAGE6}/01_tail_alpha_summary.csv")
        latest_digest = read_csv_from_zip(zf, f"{STAGE6}/02_latest_tail_group_summary.csv")
        horserace_digest = read_csv_from_zip(zf, f"{STAGE6}/03_stage2_horserace_summary.csv")
        main_table_digest = read_csv_from_zip(
            zf, f"{STAGE6}/04_stage2_future_tail_event_main_table.csv"
        )
        stage5_digest = read_csv_from_zip(zf, f"{STAGE6}/05_stage5_interaction_summary.csv")
        corr_digest = read_csv_from_zip(zf, f"{STAGE6}/06_key_correlations.csv")

        horserace_keys = {
            (r["dependent"], r["spec_name"], r["param"]) for r in horserace_digest
        }
        horserace_expected = [
            r
            for r in horserace_summary(stage2_reg)
            if (str(r["dependent"]), str(r["spec_name"]), str(r["param"]))
            in horserace_keys
        ]

        stage5_keys = {(r["dependent"], r["spec"], r["param"]) for r in stage5_digest}
        stage5_expected = [
            r
            for r in stage5_summary(stage5_reg)
            if (str(r["dependent"]), str(r["spec"]), str(r["param"])) in stage5_keys
        ]

        checks = [
            (
                "tail alpha summary from raw Stage4",
                tail_alpha_summary(tail_raw),
                tail_digest,
                ["window"],
                list(tail_digest[0].keys())[1:],
            ),
            (
                "latest tail summary from raw Stage4",
                latest_tail_summary(latest_raw),
                latest_digest,
                ["window"],
                list(latest_digest[0].keys())[1:],
            ),
            (
                "Stage2 horse-race from raw HAC regressions",
                horserace_expected,
                horserace_digest,
                ["dependent", "spec_name", "param"],
                list(horserace_digest[0].keys())[3:],
            ),
            (
                "Stage5 interaction summary from raw regressions",
                stage5_expected,
                stage5_digest,
                ["dependent", "spec", "param"],
                list(stage5_digest[0].keys())[3:],
            ),
        ]

        for args in checks:
            n, f_ = check_rows(*args, tol=1e-8)
            notes.extend(n)
            failures.extend(f_)

        # Main table and key correlations are direct archive-digest selections
        # from Stage2/Stage5 raw outputs. Check exact row keys and core values.
        main_raw = [
            r
            for r in stage2_reg
            if r["dependent"] == "future_tail_event"
            and r["param"] in {"dq_es", "dr_es_concentration"}
        ]
        n, f_ = check_rows(
            "Stage2 future_tail_event main table from raw HAC regressions",
            main_raw,
            main_table_digest,
            ["market", "period", "window", "horizon", "tail_prob", "spec_name", "param"],
            ["n_obs", "r2", "coef", "std_err_hac", "t_hac", "pvalue_hac"],
            tol=1e-10,
        )
        notes.extend(n)
        failures.extend(f_)

        n, f_ = check_rows(
            "Stage5 key correlations from raw correlation table",
            stage5_corr,
            corr_digest,
            ["period", "window", "horizon", "tail_prob", "var1", "var2"],
            ["corr", "n_obs"],
            tol=1e-10,
        )
        notes.extend(n)
        failures.extend(f_)

        notes.append("standalone Stage6 digest comparison:")
        notes.extend(compare_standalone_stage6(zf))

    status = "PASS" if not failures else "FAIL"
    report = [
        "# Archive Data Audit",
        "",
        "Date: 2026-06-02",
        "",
        f"Status: **{status}**",
        "",
        "## Scope",
        "",
        "This audit rereads the canonical archived research bundle directly:",
        "",
        f"- `{ARCHIVE.name}`",
        "",
        "It does not use derived local `article/tables/*.csv` as the source of truth.",
        "The archive stores research outputs as CSV internally, so the audit parses",
        "those files from inside the ZIP without extracting or relying on generated",
        "local tables.",
        "",
        "## Checks",
        "",
    ]
    report.extend(f"- {line}" for line in notes)
    report.extend(["", "## Result", ""])
    if failures:
        report.append("Archive audit found mismatches:")
        report.extend(f"- {line}" for line in failures)
    else:
        report.append(
            "No mismatches found between raw archived Stage4/Stage2/Stage5 outputs "
            "and the assetwise Stage6 digest used by the coursework."
        )
        report.append("")
        report.append(
            "Important note: standalone `moex_stage6_article_digest.zip` differs "
            "from the assetwise bundle for Stage5 interaction/correlation files, "
            "so the canonical source for the coursework should remain "
            "`moex_article_core_assetwise_20260524_1008.zip`."
        )
    report.append("")
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"Archive audit {status}; report written to {REPORT}")
    if failures:
        print("\n".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
