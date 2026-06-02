# DQ Coursework Project State

Last updated: 2026-06-02

Owner: Dima

## Final Objective

Produce a finished coursework paper, not just an audit:

- coherent Russian academic text;
- corrected DQ/DR and heavy-tail theory;
- formulas checked against primary sources;
- empirical section based on reproducible Stage2/Stage4/Stage5/Stage6 results;
- selected article-ready figures and tables;
- final export target: DOCX.

## Current Working Branch

Repository: `/home/openclaw/.openclaw/workspace/dq-heavy-tails`

Branch: `coursework-cleanup-first-pass`

Local commit already made:

- `380c8d4 chore: add first-pass coursework structure`
- `07a5689 docs: start coursework manuscript draft`
- `719220a docs: record final coursework requirements`
- `a87c4b5 docs: verify DQ literature and notation`

No GitHub push has been made.

Push policy:

- No push during drafting.
- Push only one final version after the DOCX is ready and Dima approves.

## Durable Work Setup

Background work:

- Literature/formula verification subtask started as `dq_coursework_literature`.
- Recurring continuation cron created: `dq-coursework-continuation`, every 2 hours.

DOCX tooling:

- Pandoc 3.9.0.2 is installed locally for the OpenClaw user.
- `pandoc` resolves through `/home/openclaw/.npm-global/bin/pandoc`.

Rules:

- Do not push to GitHub during drafting.
- Push only the final approved version when the DOCX is ready.
- Do not rewrite Git history without explicit permission.
- Do not delete large tracked artifacts until canonical reproducibility bundle is chosen.
- Prefer small local commits after self-contained, verified work blocks.

## User Requirements Confirmed

- Time: no hard time limit; more than 24 hours available. Prioritize quality over speed.
- Final format: DOCX.
- Department/template requirements: none provided.
- Title page details: not needed for now.
- GitHub: no push until final; push only one final version after the DOCX is ready.

## Empirical Direction

The original `alpha < 1` superiority framing is not supported by the current data.

Current defensible thesis:

> For liquid MOEX equities, Diversification Quotient contains predictive information about future tail-event incidence beyond the classical Diversification Ratio. Conservative EVT estimation shows that ultra-heavy `alpha < 1` regimes are empirically rare in this sample, while DQ remains strongly connected with portfolio-level tail-heaviness measures. Therefore DQ should be interpreted as a tail-sensitive diversification diagnostic and predictive signal, and alpha-conditioned interaction models should be treated as robustness evidence because of collinearity.

## Immediate Next Blocks

1. Continue expanding `manuscript/coursework.md` from running draft to full coursework length.
2. Add a reproducible DOCX build target/script instead of ad hoc pandoc commands.
3. Polish discussion, limitations, conclusion and references.
4. Decide whether to include title page later; current requirement says no title page for now.
5. Keep final GitHub push blocked until DOCX is complete and Dima approves.

## Completed Work Blocks

- DQ/DR/EVT literature and formula verification is recorded in `docs/LITERATURE_AND_FORMULAS_2026-06-01.md`.
- The manuscript now uses Han-Lin-Wang as the primary DQ source and treats Han-Lin-Zhao only as an empirical-estimator reference.
- The manuscript distinguishes classical volatility DR from the ES concentration ratio implemented in the empirical pipeline.
- Stage6 digest tables are converted into compact paper tables in `article/tables/` by `pipeline/prepare_coursework_tables.py`.
- The manuscript methodology/results sections now include regression design, selected tables and selected figures.
- Pandoc DOCX smoke/progress build succeeds; latest progress DOCX is in `build/`.
