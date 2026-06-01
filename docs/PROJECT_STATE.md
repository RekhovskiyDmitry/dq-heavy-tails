# DQ Coursework Project State

Last updated: 2026-06-01

Owner: Dima

## Final Objective

Produce a finished coursework paper, not just an audit:

- coherent Russian academic text;
- corrected DQ/DR and heavy-tail theory;
- formulas checked against primary sources;
- empirical section based on reproducible Stage2/Stage4/Stage5/Stage6 results;
- selected article-ready figures and tables;
- final export target to be confirmed: DOCX/PDF/LaTeX.

## Current Working Branch

Repository: `/home/openclaw/.openclaw/workspace/dq-heavy-tails`

Branch: `coursework-cleanup-first-pass`

Local commit already made:

- `380c8d4 chore: add first-pass coursework structure`

No GitHub push has been made.

## Durable Work Setup

Background work:

- Literature/formula verification subtask started as `dq_coursework_literature`.
- Recurring continuation cron created: `dq-coursework-continuation`, every 4 hours.

Rules:

- Do not push to GitHub without explicit permission.
- Do not rewrite Git history without explicit permission.
- Do not delete large tracked artifacts until canonical reproducibility bundle is chosen.
- Prefer small local commits after self-contained, verified work blocks.

## Empirical Direction

The original `alpha < 1` superiority framing is not supported by the current data.

Current defensible thesis:

> For liquid MOEX equities, Diversification Quotient contains predictive information about future tail-event incidence beyond the classical Diversification Ratio. Conservative EVT estimation shows that ultra-heavy `alpha < 1` regimes are empirically rare in this sample, while DQ remains strongly connected with portfolio-level tail-heaviness measures. Therefore DQ should be interpreted as a tail-sensitive diversification diagnostic and predictive signal, and alpha-conditioned interaction models should be treated as robustness evidence because of collinearity.

## Critical Open Questions For Dima

Ask only if not already answered:

1. Required final format: DOCX, PDF, LaTeX, or all of them?
2. Required volume and formatting: pages, font, line spacing, ГОСТ/department template?
3. Deadline.
4. Title-page details: university, faculty, course, teacher, group, name spelling.
5. Whether pushing to GitHub is allowed, and whether force-push/history rewrite is allowed later.

## Immediate Next Blocks

1. Verify DQ formula and citations.
2. Build `manuscript/coursework.md` into a real running draft.
3. Convert Stage6 digest tables into final paper tables.
4. Polish and select 3-4 figures for final paper.
5. Rewrite introduction, methodology, results, discussion, conclusion.
