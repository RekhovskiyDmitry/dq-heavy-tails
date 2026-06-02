# Final Coursework Audit

Date: 2026-06-02 09:13 UTC

Domain: DOCX export and final audit.

## Scope

This audit checks the current coursework candidate against the final delivery
requirements:

- Russian coursework manuscript is present;
- table and figure captions are explicit in the DOCX source;
- references are not empty or placeholder-only;
- manuscript has no obvious TODO/FIXME/placeholder tokens;
- referenced PNG figures exist;
- final DOCX builds reproducibly through `scripts/build_coursework_docx.sh`;
- final DOCX is a valid Word zip package and embeds the expected figures.

## Canonical Candidate

- Manuscript: `manuscript/coursework.md`
- DOCX: `build/coursework-final.docx`
- Build command: `scripts/build_coursework_docx.sh build/coursework-final.docx`
- Audit command: `scripts/audit_coursework_final.sh build/coursework-final.docx`

## Observed Audit Metrics

Last observed audit pass: 2026-06-02 18:15 UTC.

- word count: 4577;
- references: 17;
- explicit table captions: 3;
- explicit figure captions: 3;
- embedded DOCX media files: 3;
- Word math objects in DOCX XML: 118;
- traceability table rows checked against article artifacts: 16;
- traceability prose values checked against article artifacts: 10;
- archive-data audit from canonical ZIP: passed;
- repeated adjacent words: 0;
- punctuation artifacts from the audit pattern: 0;
- raw TeX markers checked in DOCX XML: none for `\operatorname`,
  `\frac`, `\alpha`, `\sum`, `\mathrm`.

Additional 15:17 UTC verification:

- `scripts/audit_coursework_final.sh` now runs
  `scripts/audit_coursework_traceability.py`, which checks manuscript table
  rows and selected prose values against the Stage6/article table artifacts
  for tail-alpha distribution, latest tail classification, horse-race
  regressions, selected representative regression and key correlations;
- `build/coursework-final.docx` rebuilt successfully and remains the canonical
  DOCX candidate;
- the DOCX is generated under ignored `build/`, so the file is available
  locally but is not part of the current Git history unless explicitly added
  during the final approved delivery step.

Additional 16:14 UTC verification:

- `scripts/audit_coursework_final.sh build/coursework-final.docx` passed again;
- the final DOCX was rebuilt successfully;
- the audit still reports 4577 words, 17 references, 3 table captions, 3 figure
  captions, 3 embedded media files and 118 Word math objects;
- no manuscript or export-formatting changes were required.

Additional 17:14 UTC verification:

- `scripts/audit_coursework_final.sh build/coursework-final.docx` passed again;
- the final DOCX was rebuilt successfully;
- the audit still reports 4577 words, 17 references, 3 table captions, 3 figure
  captions, 3 embedded media files and 118 Word math objects;
- traceability still checks 16 table rows and 10 prose values against the
  Stage6/article artifacts;
- no manuscript, table, figure, formula or export-formatting changes were
  required.

Additional 17:27 UTC archive-data verification:

- added `scripts/audit_coursework_archive_data.py`;
- the audit reads `moex_article_core_assetwise_20260524_1008.zip` directly,
  without using generated local `article/tables/*.csv` as the source of truth;
- it recomputes/checks Stage4 tail-alpha summaries, latest tail membership,
  Stage2 horse-race summaries, Stage2 `future_tail_event` main-table rows,
  Stage5 interaction summaries and Stage5 key correlations from archived raw
  outputs;
- checks passed against the assetwise Stage6 digest: 3 tail summary rows, 3
  latest membership rows, 40 horse-race rows, 60 Stage5 interaction rows, 192
  Stage2 main-table rows and 192 key-correlation rows;
- standalone `moex_stage6_article_digest.zip` differs from the assetwise bundle
  for Stage5 interaction/correlation artifacts, so the canonical empirical
  archive for this coursework remains `moex_article_core_assetwise_20260524_1008.zip`.

Additional 18:15 UTC verification:

- `scripts/audit_coursework_final.sh build/coursework-final.docx` passed again;
- the final DOCX was rebuilt successfully and remains the canonical candidate;
- the audit still reports 4577 words, 17 references, 3 table captions, 3 figure
  captions, 3 embedded media files and 118 Word math objects;
- traceability still checks 16 table rows and 10 prose values against the
  Stage6/article artifacts;
- the archive-data gate reread `moex_article_core_assetwise_20260524_1008.zip`
  and passed;
- no manuscript, table, figure, formula, traceability or export-formatting
  changes were required.

## Scientific Claim Check

The manuscript keeps the conservative empirical thesis:

- strict `alpha_tail < 1` is not used as the central empirical result;
- DQ is framed as predictive content for future tail-event incidence and as a
  tail-sensitive diversification diagnostic;
- alpha-conditioned models are treated as robustness evidence because DQ and
  tail-heaviness are highly collinear.

## Remaining External Gate

No GitHub push is allowed until Dima reviews the DOCX candidate and explicitly
approves the final push.
