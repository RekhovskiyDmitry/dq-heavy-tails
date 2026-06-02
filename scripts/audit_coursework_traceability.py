#!/usr/bin/env python3
"""Check that manuscript result values still match article table artifacts."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript" / "coursework.md"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def normalize_text(value: str) -> str:
    value = value.replace(r"$\alpha_{\mathrm{tail}}$", "alpha_tail")
    value = value.replace(r"$R^2$", "R2")
    value = re.sub(r"(?<=\d),(?=\d)", ".", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def markdown_data_rows(path: Path) -> list[tuple[str, ...]]:
    if not path.is_file():
        fail(f"missing table artifact: {path.relative_to(ROOT)}")

    rows: list[tuple[str, ...]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            continue

        cells = tuple(normalize_text(cell) for cell in line.strip("|").split("|"))
        if not cells:
            continue

        joined = "".join(cells).replace(" ", "")
        if set(joined) <= {"-", ":"}:
            continue
        if cells[0] in {"Окно, дней", "Спецификация", "Пара переменных"}:
            continue

        rows.append(cells)

    return rows


def manuscript_rows() -> set[tuple[str, ...]]:
    return set(markdown_data_rows(MANUSCRIPT))


def check_embedded_tables(manuscript_table_rows: set[tuple[str, ...]]) -> int:
    row_count = 0
    source_tables = [
        ROOT / "article" / "tables" / "01_tail_alpha_summary.md",
        ROOT / "article" / "tables" / "03_future_tail_horserace.md",
        ROOT / "article" / "tables" / "05_correlation_summary.md",
    ]

    for source_table in source_tables:
        for row in markdown_data_rows(source_table):
            row_count += 1
            if row not in manuscript_table_rows:
                fail(
                    "manuscript table row does not match "
                    f"{source_table.relative_to(ROOT)}: {row}"
                )

    return row_count


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        fail(f"missing CSV artifact: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def check_latest_tail_summary(manuscript_text: str) -> int:
    checked = 0
    rows = markdown_data_rows(ROOT / "article" / "tables" / "02_latest_tail_summary.md")
    for row in rows:
        median_alpha = row[2]
        strict_above_two = row[8]
        for value in (median_alpha, strict_above_two):
            checked += 1
            if value not in manuscript_text:
                fail(
                    "latest tail summary value is absent from manuscript prose: "
                    f"{value}"
                )
    return checked


def check_representative_regression(manuscript_text: str) -> int:
    checked = 0
    rows = read_csv_rows(ROOT / "article" / "tables" / "04_selected_tail_regression.csv")
    wanted = {
        ("dq_dr", "dq_es"),
        ("dq_dr", "dr_es_concentration"),
    }

    for row in rows:
        key = (row["Спецификация"], row["Переменная"])
        if key not in wanted:
            continue

        match = re.fullmatch(r"(-?\d+\.\d+) \((-?\d+\.\d+)\)", row["Коэф. (t_HAC)"])
        if not match:
            fail(f"cannot parse representative coefficient cell for {key}")

        for value in match.groups():
            checked += 1
            if value not in manuscript_text:
                fail(f"representative regression value is absent from manuscript prose: {value}")

    if checked != 4:
        fail("representative regression audit did not check the expected four values")

    return checked


def main() -> None:
    if not MANUSCRIPT.is_file():
        fail(f"missing manuscript: {MANUSCRIPT.relative_to(ROOT)}")

    text = normalize_text(MANUSCRIPT.read_text(encoding="utf-8"))
    row_count = check_embedded_tables(manuscript_rows())
    latest_count = check_latest_tail_summary(text)
    regression_count = check_representative_regression(text)

    print(f"traceability_table_rows={row_count}")
    print(f"traceability_prose_values={latest_count + regression_count}")
    print("Traceability audit passed")


if __name__ == "__main__":
    main()
