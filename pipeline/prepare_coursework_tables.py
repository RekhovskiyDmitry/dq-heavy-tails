#!/usr/bin/env python3
"""Prepare compact tables for the coursework manuscript.

The script reads Stage 6 digest CSV files and writes article-ready CSV and
Markdown tables into article/tables/. It deliberately uses only the standard
library so the coursework export layer can run even before the full research
environment is installed.
"""

from __future__ import annotations

import csv
from pathlib import Path
from statistics import median
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DIGEST = ROOT / "article" / "stage6_digest"
OUT = ROOT / "article" / "tables"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt_num(x: object, digits: int = 3) -> str:
    if x is None or x == "":
        return ""
    return f"{float(x):.{digits}f}"


def fmt_p(x: object) -> str:
    if x is None or x == "":
        return ""
    value = float(x)
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def csv_quote(value: str) -> str:
    if any(ch in value for ch in [",", '"', "\n"]):
        return '"' + value.replace('"', '""') + '"'
    return value


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    columns = list(rows[0].keys())
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(csv_quote(str(row[col])) for col in columns))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, str]]) -> str:
    columns = list(rows[0].keys())
    widths = {
        col: max(len(col), *(len(str(row[col])) for row in rows))
        for col in columns
    }
    header = "| " + " | ".join(col.ljust(widths[col]) for col in columns) + " |"
    divider = "| " + " | ".join("-" * widths[col] for col in columns) + " |"
    body = [
        "| " + " | ".join(str(row[col]).ljust(widths[col]) for col in columns) + " |"
        for row in rows
    ]
    return "\n".join([header, divider, *body])


def write_table(name: str, rows: list[dict[str, str]], caption: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / f"{name}.csv", rows)
    md = f"**{caption}**\n\n" + markdown_table(rows) + "\n"
    (OUT / f"{name}.md").write_text(md, encoding="utf-8")


def project(row: dict[str, str], mapping: list[tuple[str, str]]) -> dict[str, str]:
    return {new_name: row[old_name] for old_name, new_name in mapping}


def tail_alpha_summary() -> list[dict[str, str]]:
    rows = read_rows(DIGEST / "01_tail_alpha_summary.csv")
    mapping = [
        ("window", "Окно, дней"),
        ("n_estimates", "N оценок"),
        ("alpha_median", "Медиана alpha_tail"),
        ("alpha_p10", "p10"),
        ("alpha_p25", "p25"),
        ("alpha_p75", "p75"),
        ("point_alpha_lt1", "Точечно <1"),
        ("point_alpha_1_2", "Точечно 1-2"),
        ("strict_alpha_lt1", "Строго <1"),
        ("strict_alpha_gt2", "Строго >2"),
    ]
    out = [project(row, mapping) for row in rows]
    for row in out:
        for col in ["Медиана alpha_tail", "p10", "p25", "p75"]:
            row[col] = fmt_num(row[col], 2)
    return out


def latest_tail_summary() -> list[dict[str, str]]:
    rows = read_rows(DIGEST / "02_latest_tail_group_summary.csv")
    mapping = [
        ("window", "Окно, дней"),
        ("n_securities", "N бумаг"),
        ("alpha_median", "Медиана alpha_tail"),
        ("alpha_p10", "p10"),
        ("alpha_p25", "p25"),
        ("alpha_p75", "p75"),
        ("point_alpha_1_2", "Точечно 1-2"),
        ("point_alpha_gt2", "Точечно >2"),
        ("strict_alpha_gt2", "Строго >2"),
        ("mean_p_alpha_gt2", "Средн. P(alpha>2)"),
    ]
    out = [project(row, mapping) for row in rows]
    for row in out:
        for col in ["Медиана alpha_tail", "p10", "p25", "p75", "Средн. P(alpha>2)"]:
            row[col] = fmt_num(row[col], 2)
    return out


def future_tail_horserace() -> list[dict[str, str]]:
    rows = [
        row
        for row in read_rows(DIGEST / "03_stage2_horserace_summary.csv")
        if row["dependent"] == "future_tail_event"
    ]
    order = [
        ("dq_only", "dq_es"),
        ("dr_only", "dr_es_concentration"),
        ("dq_dr", "dq_es"),
        ("dq_dr", "dr_es_concentration"),
        ("dq_dr_current_es", "dq_es"),
        ("dq_dr_current_es", "dr_es_concentration"),
        ("full", "dq_es"),
        ("full", "dr_es_concentration"),
    ]
    selected = []
    for spec, param in order:
        selected.extend(
            row for row in rows if row["spec_name"] == spec and row["param"] == param
        )

    out = []
    for row in selected:
        out.append(
            {
                "Спецификация": row["spec_name"],
                "Переменная": row["param"],
                "N моделей": row["n_models"],
                "Значимо 5%": row["sig5"],
                "+ / - на 10%": f"{row['pos_sig10']} / {row['neg_sig10']}",
                "Медиан. коэф.": fmt_num(row["median_coef"], 3),
                "Медиан. t(HAC)": fmt_num(row["median_t_hac"], 3),
                "Средн. R2": fmt_num(row["mean_r2"], 3),
            }
        )
    return out


def selected_tail_regression() -> list[dict[str, str]]:
    specs = {"dq_only", "dr_only", "dq_dr", "dq_dr_current_es", "full"}
    rows = [
        row
        for row in read_rows(DIGEST / "04_stage2_future_tail_event_main_table.csv")
        if row["period"] == "baseline_2018"
        and row["window"] == "504"
        and row["horizon"] == "21"
        and row["tail_prob"] == "0.025"
        and row["spec_name"] in specs
    ]
    return [
        {
            "Спецификация": row["spec_name"],
            "Переменная": row["param"],
            "Коэф. (t_HAC)": f"{fmt_num(row['coef'], 3)} ({fmt_num(row['t_hac'], 2)})",
            "p-value": fmt_p(row["pvalue_hac"]),
            "R2": fmt_num(row["r2"], 3),
            "N": row["n_obs"],
        }
        for row in rows
    ]


def values(rows: Iterable[dict[str, str]], var1: str, var2: str) -> list[float]:
    return [
        float(row["corr"])
        for row in rows
        if row["var1"] == var1 and row["var2"] == var2 and row["corr"] != ""
    ]


def correlation_summary() -> list[dict[str, str]]:
    rows = read_rows(DIGEST / "06_key_correlations.csv")
    pairs = [
        ("dq_es", "alpha_heaviness_inv", "DQ и обратная alpha_tail"),
        ("dq_es", "alpha_median", "DQ и медианная alpha_tail"),
        ("dq_es", "dr_es_concentration", "DQ и ES concentration ratio"),
        ("dq_es", "future_tail_event", "DQ и future tail event"),
        (
            "dr_es_concentration",
            "future_tail_event",
            "Concentration ratio и future tail event",
        ),
    ]
    out = []
    for var1, var2, label in pairs:
        series = values(rows, var1, var2)
        out.append(
            {
                "Пара переменных": label,
                "N спецификаций": str(len(series)),
                "Медиана corr": fmt_num(median(series), 3),
                "Мин. corr": fmt_num(min(series), 3),
                "Макс. corr": fmt_num(max(series), 3),
            }
        )
    return out


def main() -> None:
    tables = [
        (
            "01_tail_alpha_summary",
            tail_alpha_summary(),
            "Табл. 1. Распределение оценок хвостового индекса по длине окна",
        ),
        (
            "02_latest_tail_summary",
            latest_tail_summary(),
            "Табл. 2. Последняя классификация бумаг по хвостовому индексу",
        ),
        (
            "03_future_tail_horserace",
            future_tail_horserace(),
            "Табл. 3. Значимость DQ и ES concentration ratio в моделях future_tail_event",
        ),
        (
            "04_selected_tail_regression",
            selected_tail_regression(),
            "Табл. 4. Репрезентативная регрессия future_tail_event",
        ),
        (
            "05_correlation_summary",
            correlation_summary(),
            "Табл. 5. Корреляции DQ с tail-heaviness и будущими хвостовыми событиями",
        ),
    ]
    combined = []
    for name, rows, caption in tables:
        write_table(name, rows, caption)
        combined.append(f"## {caption}\n\n{markdown_table(rows)}\n")
    (OUT / "coursework_tables.md").write_text("\n".join(combined), encoding="utf-8")
    print(f"Wrote {len(tables)} tables to {OUT}")


if __name__ == "__main__":
    main()
