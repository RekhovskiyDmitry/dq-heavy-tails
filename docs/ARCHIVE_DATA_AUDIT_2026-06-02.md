# Archive Data Audit

Date: 2026-06-02

Status: **PASS**

## Scope

This audit rereads the canonical archived research bundle directly:

- `moex_article_core_assetwise_20260524_1008.zip`

It does not use derived local `article/tables/*.csv` as the source of truth.
The archive stores research outputs as CSV internally, so the audit parses
those files from inside the ZIP without extracting or relying on generated
local tables.

## Checks

- canonical archive: moex_article_core_assetwise_20260524_1008.zip
- archive entries: 53
- Stage4 raw tail estimates rows: 43377
- Stage4 latest membership rows: 426
- Stage2 HAC regression rows: 3240
- Stage5 interaction regression rows: 5200
- Stage5 correlation rows: 192
- tail alpha summary from raw Stage4: checked 3 rows against archive digest
- latest tail summary from raw Stage4: checked 3 rows against archive digest
- Stage2 horse-race from raw HAC regressions: checked 40 rows against archive digest
- Stage5 interaction summary from raw regressions: checked 60 rows against archive digest
- Stage2 future_tail_event main table from raw HAC regressions: checked 192 rows against archive digest
- Stage5 key correlations from raw correlation table: checked 192 rows against archive digest
- standalone Stage6 digest comparison:
- 01_tail_alpha_summary.csv: assetwise 22683ccfb685, standalone 22683ccfb685 -> MATCH
- 02_latest_tail_group_summary.csv: assetwise e3c4c1b8cdc3, standalone e3c4c1b8cdc3 -> MATCH
- 03_stage2_horserace_summary.csv: assetwise 9d68583e1dcd, standalone 9d68583e1dcd -> MATCH
- 04_stage2_future_tail_event_main_table.csv: assetwise 0df475b42bb5, standalone 0df475b42bb5 -> MATCH
- 05_stage5_interaction_summary.csv: assetwise 72ac135df017, standalone 404d17f8a4de -> DIFF
- 06_key_correlations.csv: assetwise 7bc89accaa44, standalone 67827dabe498 -> DIFF

## Result

No mismatches found between raw archived Stage4/Stage2/Stage5 outputs and the assetwise Stage6 digest used by the coursework.

Important note: standalone `moex_stage6_article_digest.zip` differs from the assetwise bundle for Stage5 interaction/correlation files, so the canonical source for the coursework should remain `moex_article_core_assetwise_20260524_1008.zip`.
