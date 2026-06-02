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

Last observed audit pass: 2026-06-02 15:17 UTC.

- word count: 4577;
- references: 17;
- explicit table captions: 3;
- explicit figure captions: 3;
- embedded DOCX media files: 3;
- Word math objects in DOCX XML: 118;
- traceability table rows checked against article artifacts: 16;
- traceability prose values checked against article artifacts: 10;
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
