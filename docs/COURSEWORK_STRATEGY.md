# Coursework Strategy

Last updated: 2026-06-02

## Operating Mode

The coursework is handled as a sequence of strategic work blocks, not as
opportunistic edits.

Cadence:

- Recurring background run every 60 minutes.
- Each run is allowed to be long; do not rush to produce a tiny diff.
- At least half of each run's effort should go into strategy, audit,
  sequencing, consistency checks, and deciding the next highest-leverage block.
- The remaining effort should implement one coherent domain block.

Every run must start by reading:

1. `docs/PROJECT_STATE.md`
2. `docs/COURSEWORK_STRATEGY.md`
3. `manuscript/coursework.md`
4. `git status --short --branch`

Every run must end with:

1. a short Telegram update to Dima;
2. a clear next block;
3. a local commit if the work block is self-contained and verified;
4. a DOCX checkpoint when manuscript content or export formatting changed.

## Non-Chaotic Work Rule

Do one main domain per run. Do not jump across unrelated areas just because
many files are available.

Allowed domain types:

- strategy and structure;
- theoretical framework;
- data and reproducibility;
- empirical methodology;
- empirical results;
- interpretation and limitations;
- references and citations;
- DOCX export and formatting;
- final audit.

If a run discovers a blocker outside the chosen domain, record it and continue
the current domain unless the blocker makes progress impossible.

## Current Scientific Thesis

The original `alpha < 1` superiority framing is not supported by the current
MOEX data. The defensible thesis is:

> For liquid MOEX equities, DQ contains predictive information about future
> tail-event incidence and acts as a tail-sensitive diversification diagnostic.
> Conservative EVT estimation finds no strict `alpha < 1` regime in the sample,
> so alpha-conditioned interaction models are robustness evidence rather than
> the central identification result.

## Target Paper Shape

The final Russian coursework should contain:

1. abstract and keywords;
2. introduction with problem, goal, tasks, contribution, and honest hypothesis
   revision;
3. theory: risk measures, DR/ES concentration ratio, DQ, heavy tails, EVT;
4. data and methodology: MOEX total-return returns, rolling windows, tail-index
   estimation, portfolio metrics, regression design;
5. results: tail-index distribution, DQ/DR horse-race, DQ and tail-heaviness,
   figures and compact tables;
6. discussion: why `alpha < 1` is not found, what DQ still contributes,
   collinearity, limitations;
7. conclusion;
8. references;
9. optional reproducibility appendix if needed.

## Quality Gates

Before calling the coursework close to final:

- no placeholder phrases such as "final version should";
- formulas render through Pandoc into DOCX;
- tables are compact enough for DOCX;
- figures are referenced and interpretable in surrounding text;
- DQ source attribution is correct: Han-Lin-Wang for DQ, Han-Lin-Zhao only for
  empirical-estimator discussion;
- DR terminology is not misleading: the implemented metric is ES concentration
  ratio, not classical volatility DR;
- no central claim depends on strict `alpha < 1`;
- all empirical claims used in the text are traceable to Stage2/Stage4/Stage5/
  Stage6 outputs;
- DOCX builds successfully;
- GitHub is not pushed until Dima approves the final DOCX.

## Next Strategic Sequence

### Block 1: Structure And Gap Audit

Goal: produce a section-by-section gap map for `manuscript/coursework.md`.

Checks:

- word count by section;
- missing academic transitions;
- weak claims needing source/table support;
- duplicated or underexplained points;
- list of final tables and figures.

Output:

- update this strategy if priorities change;
- no large prose rewrite unless the audit clearly identifies the next section.

### Block 2: Theory Polish

Goal: make the theoretical section academically smooth and citation-ready.

Focus:

- risk measures and ES;
- DR vs ES concentration ratio;
- DQ definition and interpretation;
- heavy-tail regimes and EVT estimators.

Output:

- polished section 2;
- DOCX checkpoint.

### Block 3: Methodology Polish

Goal: make section 3 read as research methodology, not pipeline notes.

Focus:

- data source and total-return logic;
- sample construction;
- rolling windows;
- dependent variables;
- HAC/Newey-West rationale;
- reproducibility appendix boundary.

Output:

- polished section 3;
- optional build script for DOCX.

### Block 4: Results Deepening

Goal: turn section 4 from a result summary into a persuasive empirical story.

Focus:

- table-by-table interpretation;
- figure-by-figure interpretation;
- explain signs and economic meaning;
- avoid overclaiming on alpha interactions.

Output:

- expanded section 4;
- checked table/figure references.

### Block 5: Discussion, Limitations, Conclusion

Goal: finish the argument.

Status: completed in the 2026-06-02 07:14 UTC continuation block.

Focus:

- revised hypothesis;
- what the negative alpha result means;
- why DQ still matters;
- limitations and future work;
- concise conclusion.

Output:

- polished sections 5 and 6.
- DOCX checkpoint `build/coursework-progress-2026-06-02-0714.docx`.

### Block 6: DOCX And Final Audit

Goal: make the final artifact.

Focus:

- reference formatting;
- figure/table layout;
- spell and placeholder audit;
- final DOCX export.

Status:

- reproducible DOCX build script added: `scripts/build_coursework_docx.sh`;
- current canonical output path: `build/coursework-final.docx`.
- final audit script added: `scripts/audit_coursework_final.sh`;
- final audit passed and note added: `docs/FINAL_AUDIT_2026-06-02.md`;
- table and figure captions are explicit in the manuscript.

Remaining focus:

- Dima review of `build/coursework-final.docx`;
- optional title page only if Dima later asks for it;
- final GitHub push only after explicit approval.

Output:

- final DOCX candidate;
- local commit;
- Telegram summary for Dima.
